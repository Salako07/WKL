# courses/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from datetime import timedelta
from django.utils import timezone

from .models import (
    CourseCategory, Course, Module, Lesson, Exercise, 
    CourseEnrollment, LessonProgress, ExerciseSubmission
)
from .serializers import (
    CourseCategorySerializer, CourseSerializer, DetailedCourseSerializer,
    ModuleSerializer, DetailedModuleSerializer, LessonSerializer, 
    DetailedLessonSerializer, ExerciseSerializer, DetailedExerciseSerializer,
    CourseEnrollmentSerializer, LessonProgressSerializer, 
    ExerciseSubmissionSerializer, CreateExerciseSubmissionSerializer
)


class CourseCategoryViewSet(viewsets.ModelViewSet):
    """API endpoints for course categories"""
    queryset = CourseCategory.objects.filter(is_active=True)
    serializer_class = CourseCategorySerializer
    permission_classes = [permissions.AllowAny]  # Categories are public
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['parent', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']
    
    def get_permissions(self):
        """Only admins and instructors can create/update/delete categories"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
            # Add additional permission check for admin/instructor roles
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def courses(self, request, pk=None):
        """Get all courses in this category"""
        category = self.get_object()
        courses = Course.objects.filter(
            category=category, 
            status='published'
        ).order_by('-created_at')
        
        serializer = CourseSerializer(courses, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get category tree structure"""
        categories = self.get_queryset().filter(parent=None)
        data = []
        
        for category in categories:
            category_data = CourseCategorySerializer(category).data
            category_data['children'] = CourseCategorySerializer(
                category.coursecategory_set.filter(is_active=True),
                many=True
            ).data
            data.append(category_data)
        
        return Response(data)


class CourseViewSet(viewsets.ModelViewSet):
    """API endpoints for courses"""
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]  # Public courses viewable by all
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'difficulty_level', 'category', 'is_free', 'status', 
        'programming_languages', 'instructor'
    ]
    search_fields = ['title', 'description', 'tags', 'skills_gained']
    ordering_fields = [
        'created_at', 'total_enrollments', 'average_rating', 
        'completion_rate', 'estimated_duration'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter courses based on user permissions"""
        user = self.request.user
        
        if user.is_authenticated and user.can_teach:
            # Instructors can see their own courses regardless of status
            return Course.objects.filter(
                Q(status='published') | Q(instructor=user)
            ).distinct()
        else:
            # Public users can only see published courses
            return Course.objects.filter(status='published')
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve action"""
        if self.action == 'retrieve':
            return DetailedCourseSerializer
        return CourseSerializer
    
    def get_permissions(self):
        """Permission-based access control"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Set instructor as current user when creating course"""
        serializer.save(instructor=self.request.user)
    
    def perform_update(self, serializer):
        """Only allow instructors to update their own courses"""
        course = self.get_object()
        if course.instructor != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only edit your own courses")
        serializer.save()
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def enroll(self, request, pk=None):
        """Enroll user in a course"""
        course = self.get_object()
        user = request.user
        
        if not course.can_enroll(user):
            return Response(
                {'error': 'Cannot enroll in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        enrollment, created = CourseEnrollment.objects.get_or_create(
            student=user,
            course=course,
            defaults={'enrollment_source': 'direct'}
        )
        
        if created:
            # Update course enrollment count
            course.total_enrollments += 1
            course.save(update_fields=['total_enrollments'])
            
            # Create user profile if it doesn't exist
            from accounts.models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            
            return Response(
                {'message': 'Successfully enrolled in course'},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'message': 'Already enrolled in this course'},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def unenroll(self, request, pk=None):
        """Unenroll user from a course"""
        course = self.get_object()
        user = request.user
        
        try:
            enrollment = CourseEnrollment.objects.get(student=user, course=course)
            enrollment.status = 'dropped'
            enrollment.save()
            
            return Response({'message': 'Successfully unenrolled from course'})
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'Not enrolled in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def progress(self, request, pk=None):
        """Get user's progress in the course"""
        course = self.get_object()
        user = request.user
        
        try:
            enrollment = CourseEnrollment.objects.get(student=user, course=course)
            serializer = CourseEnrollmentSerializer(enrollment, context={'request': request})
            return Response(serializer.data)
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'Not enrolled in this course'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def modules(self, request, pk=None):
        """Get course modules with lessons"""
        course = self.get_object()
        modules = course.modules.prefetch_related('lessons').order_by('order')
        serializer = DetailedModuleSerializer(modules, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def rate(self, request, pk=None):
        """Rate a course"""
        course = self.get_object()
        user = request.user
        rating = request.data.get('rating')
        review = request.data.get('review', '')
        
        if not rating or not (1 <= rating <= 5):
            return Response(
                {'error': 'Rating must be between 1 and 5'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is enrolled
        if not CourseEnrollment.objects.filter(student=user, course=course).exists():
            return Response(
                {'error': 'You must be enrolled to rate this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or update course rating
        from analytics.models import CourseRating
        course_rating, created = CourseRating.objects.update_or_create(
            course=course,
            student=user,
            defaults={'rating': rating, 'review': review}
        )
        
        # Update course average rating
        avg_rating = CourseRating.objects.filter(course=course).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating']
        
        course.average_rating = avg_rating or 0
        course.total_reviews = CourseRating.objects.filter(course=course).count()
        course.save(update_fields=['average_rating', 'total_reviews'])
        
        return Response({'message': 'Course rated successfully'})
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_courses(self, request):
        """Get courses the user is enrolled in"""
        user = request.user
        enrollments = CourseEnrollment.objects.filter(
            student=user
        ).select_related('course')
        
        courses_data = []
        for enrollment in enrollments:
            course_data = CourseSerializer(enrollment.course, context={'request': request}).data
            course_data['enrollment'] = CourseEnrollmentSerializer(enrollment).data
            courses_data.append(course_data)
        
        return Response(courses_data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def teaching(self, request):
        """Get courses the user is teaching (instructors only)"""
        user = request.user
        if not user.can_teach:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        courses = Course.objects.filter(instructor=user).order_by('-created_at')
        serializer = CourseSerializer(courses, many=True, context={'request': request})
        return Response(serializer.data)


class ModuleViewSet(viewsets.ModelViewSet):
    """API endpoints for course modules"""
    serializer_class = ModuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['course', 'is_required']
    ordering_fields = ['order', 'created_at']
    ordering = ['order']
    
    def get_queryset(self):
        """Filter modules based on course access"""
        user = self.request.user
        return Module.objects.filter(
            Q(course__status='published') |
            Q(course__instructor=user) |
            Q(course__enrollments__student=user)
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DetailedModuleSerializer
        return ModuleSerializer
    
    def perform_create(self, serializer):
        """Check if user can create modules for this course"""
        course = serializer.validated_data['course']
        if course.instructor != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only create modules for your own courses")
        serializer.save()
    
    @action(detail=True, methods=['get'])
    def lessons(self, request, pk=None):
        """Get all lessons in this module"""
        module = self.get_object()
        lessons = module.lessons.order_by('order')
        serializer = LessonSerializer(lessons, many=True, context={'request': request})
        return Response(serializer.data)


class LessonViewSet(viewsets.ModelViewSet):
    """API endpoints for lessons"""
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['module', 'lesson_type', 'is_required', 'is_preview']
    search_fields = ['title', 'description', 'content']
    ordering_fields = ['order', 'created_at']
    ordering = ['order']
    
    def get_queryset(self):
        """Filter lessons based on access permissions"""
        user = self.request.user
        return Lesson.objects.filter(
            Q(module__course__status='published') |
            Q(module__course__instructor=user) |
            Q(module__course__enrollments__student=user) |
            Q(is_preview=True)  # Preview lessons are always accessible
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DetailedLessonSerializer
        return LessonSerializer
    
    def perform_create(self, serializer):
        """Check if user can create lessons"""
        module = serializer.validated_data['module']
        if module.course.instructor != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only create lessons for your own courses")
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark lesson as completed"""
        lesson = self.get_object()
        user = request.user
        
        try:
            enrollment = CourseEnrollment.objects.get(
                student=user, 
                course=lesson.module.course
            )
            
            progress, created = LessonProgress.objects.get_or_create(
                enrollment=enrollment,
                lesson=lesson,
                defaults={
                    'status': 'completed',
                    'progress_percentage': 100,
                    'completed_at': timezone.now(),
                    'first_accessed': timezone.now()
                }
            )
            
            if not created and progress.status != 'completed':
                progress.status = 'completed'
                progress.progress_percentage = 100
                progress.completed_at = timezone.now()
                if not progress.first_accessed:
                    progress.first_accessed = timezone.now()
                progress.save()
            
            # Update enrollment progress
            enrollment.lessons_completed = enrollment.lesson_progress.filter(
                status='completed'
            ).count()
            enrollment.update_progress()
            
            # Update user profile
            from accounts.models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.total_lessons_completed = LessonProgress.objects.filter(
                enrollment__student=user,
                status='completed'
            ).count()
            profile.update_streak()
            profile.save()
            
            return Response({'message': 'Lesson marked as completed'})
            
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'Not enrolled in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def bookmark(self, request, pk=None):
        """Bookmark or unbookmark a lesson"""
        lesson = self.get_object()
        user = request.user
        
        try:
            enrollment = CourseEnrollment.objects.get(
                student=user,
                course=lesson.module.course
            )
            
            progress, created = LessonProgress.objects.get_or_create(
                enrollment=enrollment,
                lesson=lesson,
                defaults={'first_accessed': timezone.now()}
            )
            
            progress.bookmarked = not progress.bookmarked
            progress.save()
            
            action = 'bookmarked' if progress.bookmarked else 'unbookmarked'
            return Response({'message': f'Lesson {action} successfully'})
            
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'Not enrolled in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def exercises(self, request, pk=None):
        """Get all exercises for this lesson"""
        lesson = self.get_object()
        exercises = lesson.exercises.order_by('order')
        serializer = ExerciseSerializer(exercises, many=True, context={'request': request})
        return Response(serializer.data)


class ExerciseViewSet(viewsets.ModelViewSet):
    """API endpoints for exercises"""
    serializer_class = ExerciseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['lesson', 'exercise_type', 'difficulty', 'programming_language']
    search_fields = ['title', 'description']
    ordering_fields = ['order', 'created_at', 'points']
    ordering = ['order']
    
    def get_queryset(self):
        """Filter exercises based on lesson access"""
        user = self.request.user
        return Exercise.objects.filter(
            Q(lesson__module__course__status='published') |
            Q(lesson__module__course__instructor=user) |
            Q(lesson__module__course__enrollments__student=user)
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DetailedExerciseSerializer
        return ExerciseSerializer
    
    def perform_create(self, serializer):
        """Check if user can create exercises"""
        lesson = serializer.validated_data['lesson']
        if lesson.module.course.instructor != self.request.user and not self.request.user.is_staff:
            raise permissions.PermissionDenied("You can only create exercises for your own courses")
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit exercise solution"""
        exercise = self.get_object()
        user = request.user
        
        # Check if user is enrolled in the course
        try:
            enrollment = CourseEnrollment.objects.get(
                student=user,
                course=exercise.lesson.module.course
            )
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'Not enrolled in this course'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check attempt limits
        existing_submissions = ExerciseSubmission.objects.filter(
            exercise=exercise,
            student=user
        )
        
        if exercise.max_attempts and existing_submissions.count() >= exercise.max_attempts:
            return Response(
                {'error': 'Maximum attempts exceeded'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create submission
        serializer = CreateExerciseSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            submission = serializer.save(
                exercise=exercise,
                student=user,
                attempt_number=existing_submissions.count() + 1
            )
            
            # TODO: Trigger code execution and grading
            # This would integrate with the code execution service
            
            response_serializer = ExerciseSubmissionSerializer(
                submission, 
                context={'request': request}
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        """Get user's submissions for this exercise"""
        exercise = self.get_object()
        user = request.user
        
        submissions = ExerciseSubmission.objects.filter(
            exercise=exercise,
            student=user
        ).order_by('-submitted_at')
        
        serializer = ExerciseSubmissionSerializer(
            submissions, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def request_hint(self, request, pk=None):
        """Request a hint for the exercise"""
        exercise = self.get_object()
        user = request.user
        
        if not exercise.ai_hints_enabled:
            return Response(
                {'error': 'Hints are not enabled for this exercise'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Integrate with AI service to generate hints
        # For now, return a placeholder
        hint = "Try breaking down the problem into smaller steps."
        
        return Response({
            'hint': hint,
            'penalty_points': exercise.hint_penalty
        })


class CourseEnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for course enrollments (read-only)"""
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'course', 'enrollment_source']
    ordering_fields = ['enrolled_at', 'progress_percentage', 'last_accessed']
    ordering = ['-enrolled_at']
    
    def get_queryset(self):
        """Users can only see their own enrollments"""
        user = self.request.user
        if user.can_teach:
            # Instructors can see enrollments for their courses
            return CourseEnrollment.objects.filter(
                Q(student=user) |
                Q(course__instructor=user)
            )
        else:
            return CourseEnrollment.objects.filter(student=user)
    
    @action(detail=True, methods=['get'])
    def progress_detail(self, request, pk=None):
        """Get detailed progress for an enrollment"""
        enrollment = self.get_object()
        
        # Get lesson progress
        lesson_progress = LessonProgress.objects.filter(
            enrollment=enrollment
        ).select_related('lesson')
        
        # Get exercise submissions
        exercise_submissions = ExerciseSubmission.objects.filter(
            student=enrollment.student,
            exercise__lesson__module__course=enrollment.course
        ).select_related('exercise')
        
        return Response({
            'enrollment': CourseEnrollmentSerializer(enrollment).data,
            'lesson_progress': LessonProgressSerializer(lesson_progress, many=True).data,
            'exercise_submissions': ExerciseSubmissionSerializer(
                exercise_submissions, many=True
            ).data
        })


class ExerciseSubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for exercise submissions (read-only)"""
    serializer_class = ExerciseSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'exercise', 'auto_graded']
    ordering_fields = ['submitted_at', 'score', 'attempt_number']
    ordering = ['-submitted_at']
    
    def get_queryset(self):
        """Filter submissions based on permissions"""
        user = self.request.user
        if user.can_teach:
            # Instructors can see submissions for their courses
            return ExerciseSubmission.objects.filter(
                Q(student=user) |
                Q(exercise__lesson__module__course__instructor=user)
            )
        else:
            return ExerciseSubmission.objects.filter(student=user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def provide_feedback(self, request, pk=None):
        """Provide instructor feedback on submission"""
        submission = self.get_object()
        user = request.user
        
        # Check if user can provide feedback
        if submission.exercise.lesson.module.course.instructor != user and not user.is_staff:
            return Response(
                {'error': 'You can only provide feedback for your own courses'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        feedback = request.data.get('feedback', '')
        score = request.data.get('score')
        
        submission.instructor_feedback = feedback
        submission.graded_by = user
        submission.graded_at = timezone.now()
        
        if score is not None and 0 <= score <= 100:
            submission.score = score
            submission.status = 'passed' if score >= 70 else 'failed'
            submission.auto_graded = False
        
        submission.save()
        
        return Response({'message': 'Feedback provided successfully'})


# Additional ViewSets for lesson progress
class LessonProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for lesson progress tracking"""
    serializer_class = LessonProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'enrollment__course', 'bookmarked']
    ordering_fields = ['first_accessed', 'last_accessed', 'completed_at']
    ordering = ['-last_accessed']
    
    def get_queryset(self):
        """Users can only see their own progress"""
        user = self.request.user
        return LessonProgress.objects.filter(enrollment__student=user)