# api/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from datetime import timedelta

# Model imports
from courses.models import Course, Lesson, Exercise, CourseEnrollment, LessonProgress, ExerciseSubmission, Module
from ai_tutor.models import AITutorSession, AIMessage
from code_execution.models import CodeExecution, ExecutionEnvironment
from collaboration.models import CollaborationRoom, RoomParticipant, ChatMessage
from analytics.models import LearningAnalytics, PerformanceMetric

# Serializer imports
from .serializers import (
    CourseSerializer, LessonSerializer, ExerciseSerializer, CourseEnrollmentSerializer,
    ExerciseSubmissionSerializer, ModuleSerializer, AITutorSessionSerializer, 
    AIMessageSerializer, CodeExecutionSerializer, ExecutionEnvironmentSerializer,
    CollaborationRoomSerializer, RoomParticipantSerializer, ChatMessageSerializer,
    LearningAnalyticsSerializer, PerformanceMetricSerializer
)


class CourseViewSet(viewsets.ModelViewSet):
    """API endpoints for courses"""
    queryset = Course.objects.filter(status='published')
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['difficulty_level', 'category', 'is_free', 'programming_languages']
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'total_enrollments', 'average_rating']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def enroll(self, request, pk=None):
        """Enroll user in a course"""
        course = self.get_object()
        
        if not course.can_enroll(request.user):
            return Response(
                {'error': 'Cannot enroll in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        enrollment, created = CourseEnrollment.objects.get_or_create(
            student=request.user,
            course=course,
            defaults={'enrollment_source': 'direct'}
        )
        
        if created:
            course.total_enrollments += 1
            course.save()
            
            return Response(
                {'message': 'Successfully enrolled in course'},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'message': 'Already enrolled in this course'},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def modules(self, request, pk=None):
        """Get course modules with lessons"""
        course = self.get_object()
        modules = course.modules.prefetch_related('lessons').order_by('order')
        serializer = ModuleSerializer(modules, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def progress(self, request, pk=None):
        """Get user's progress in the course"""
        course = self.get_object()
        
        try:
            enrollment = course.enrollments.get(student=request.user)
            serializer = CourseEnrollmentSerializer(enrollment, context={'request': request})
            return Response(serializer.data)
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'Not enrolled in this course'},
                status=status.HTTP_404_NOT_FOUND
            )


class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for lessons"""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        course_id = self.request.query_params.get('course', None)
        module_id = self.request.query_params.get('module', None)
        
        if course_id:
            queryset = queryset.filter(module__course_id=course_id)
        if module_id:
            queryset = queryset.filter(module_id=module_id)
        
        return queryset.order_by('module__order', 'order')
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark lesson as completed"""
        lesson = self.get_object()
        
        try:
            enrollment = lesson.module.course.enrollments.get(student=request.user)
            progress, created = LessonProgress.objects.get_or_create(
                enrollment=enrollment,
                lesson=lesson,
                defaults={'status': 'completed', 'progress_percentage': 100}
            )
            
            if not created and progress.status != 'completed':
                progress.status = 'completed'
                progress.progress_percentage = 100
                from django.utils import timezone
                progress.completed_at = timezone.now()
                progress.save()
                
                # Update enrollment progress
                enrollment.update_progress()
            
            return Response({'message': 'Lesson marked as completed'})
            
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'Not enrolled in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for exercises"""
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit exercise solution"""
        exercise = self.get_object()
        code = request.data.get('code', '')
        
        if not code.strip():
            return Response(
                {'error': 'Code cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check attempt limits
        existing_submissions = exercise.submissions.filter(student=request.user)
        if exercise.max_attempts and existing_submissions.count() >= exercise.max_attempts:
            return Response(
                {'error': 'Maximum attempts exceeded'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create submission
        submission = ExerciseSubmission.objects.create(
            exercise=exercise,
            student=request.user,
            submitted_code=code,
            attempt_number=existing_submissions.count() + 1,
            time_taken=timedelta(seconds=request.data.get('time_taken', 0))
        )
        
        # Execute code (integrate with CodeExecutionService)
        # This would trigger code execution and grading
        
        serializer = ExerciseSubmissionSerializer(submission, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        """Get user's submissions for this exercise"""
        exercise = self.get_object()
        submissions = exercise.submissions.filter(student=request.user).order_by('-submitted_at')
        serializer = ExerciseSubmissionSerializer(submissions, many=True, context={'request': request})
        return Response(serializer.data)


class AITutorViewSet(viewsets.ModelViewSet):
    """API endpoints for AI tutor sessions"""
    serializer_class = AITutorSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return AITutorSession.objects.filter(student=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(student=self.request.user)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get messages for a session"""
        session = self.get_object()
        messages = session.messages.order_by('created_at')
        serializer = AIMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message to the AI tutor"""
        session = self.get_object()
        content = request.data.get('content', '')
        
        if not content.strip():
            return Response(
                {'error': 'Message cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user message
        user_message = AIMessage.objects.create(
            session=session,
            message_type='user',
            content=content
        )
        
        # Generate AI response (integrate with AI service)
        # This would call the AI service to generate a response
        
        # For now, create a placeholder response
        ai_message = AIMessage.objects.create(
            session=session,
            message_type='assistant',
            content="This is a placeholder AI response. Integration with AI service needed.",
            confidence_score=0.8
        )
        
        session.total_messages += 2
        session.save()
        
        return Response({
            'user_message': AIMessageSerializer(user_message).data,
            'ai_response': AIMessageSerializer(ai_message).data
        })


class CodeExecutionViewSet(viewsets.ModelViewSet):
    """API endpoints for code execution"""
    serializer_class = CodeExecutionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CodeExecution.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def environments(self, request):
        """Get available execution environments"""
        environments = ExecutionEnvironment.objects.filter(status='active')
        serializer = ExecutionEnvironmentSerializer(environments, many=True)
        return Response(serializer.data)


class CollaborationRoomViewSet(viewsets.ModelViewSet):
    """API endpoints for collaboration rooms"""
    serializer_class = CollaborationRoomSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return CollaborationRoom.objects.filter(
            Q(creator=user) | Q(participants__user=user) | Q(is_public=True)
        ).distinct()
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a collaboration room"""
        room = self.get_object()
        
        if room.max_participants and room.participant_count >= room.max_participants:
            return Response(
                {'error': 'Room is full'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant, created = RoomParticipant.objects.get_or_create(
            room=room,
            user=request.user,
            defaults={'status': 'active'}
        )
        
        if created:
            room.participant_count += 1
            room.save()
        
        return Response({'message': 'Successfully joined room'})
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get chat messages for a room"""
        room = self.get_object()
        messages = room.chat_messages.order_by('-created_at')[:50]  # Last 50 messages
        serializer = ChatMessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)


class AnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for analytics"""
    serializer_class = LearningAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return LearningAnalytics.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard analytics data"""
        try:
            from analytics.services import AnalyticsService
            dashboard_data = AnalyticsService.get_learning_dashboard_data(request.user)
            return Response(dashboard_data)
        except ImportError:
            # Fallback if AnalyticsService is not available
            analytics, created = LearningAnalytics.objects.get_or_create(user=request.user)
            serializer = LearningAnalyticsSerializer(analytics)
            return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def performance_metrics(self, request):
        """Get performance metrics"""
        granularity = request.query_params.get('granularity', 'weekly')
        metrics = PerformanceMetric.objects.filter(
            user=request.user,
            granularity=granularity
        ).order_by('-period_start')[:20]
        
        serializer = PerformanceMetricSerializer(metrics, many=True)
        return Response(serializer.data)