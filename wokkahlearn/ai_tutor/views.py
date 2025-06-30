# ai_tutor/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from .models import (
    AIModel, AITutorSession, AIMessage, LearningPathRecommendation,
    CodeAnalysisResult, PersonalizedQuiz, AITutorFeedback
)
from .serializers import (
    AIModelSerializer, AITutorSessionSerializer, AIMessageSerializer,
    LearningPathRecommendationSerializer, CodeAnalysisResultSerializer,
    PersonalizedQuizSerializer, AITutorFeedbackSerializer
)


class AIModelViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for AI models"""
    queryset = AIModel.objects.filter(is_active=True)
    serializer_class = AIModelSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available AI models for different tasks"""
        model_type = request.query_params.get('type', None)
        queryset = self.get_queryset()
        
        if model_type:
            queryset = queryset.filter(model_type=model_type)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AITutorSessionViewSet(viewsets.ModelViewSet):
    """API endpoints for AI tutor sessions"""
    serializer_class = AITutorSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return AITutorSession.objects.filter(student=self.request.user).order_by('-started_at')
    
    def perform_create(self, serializer):
        # Get default AI model for tutoring
        ai_model = AIModel.objects.filter(
            model_type='tutor',
            is_active=True,
            is_default=True
        ).first()
        
        if not ai_model:
            ai_model = AIModel.objects.filter(
                model_type='tutor',
                is_active=True
            ).first()
        
        serializer.save(
            student=self.request.user,
            ai_model=ai_model
        )
    
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
        context = request.data.get('context', {})
        
        if not content.strip():
            return Response(
                {'error': 'Message content cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user message
        user_message = AIMessage.objects.create(
            session=session,
            message_type='user',
            content=content
        )
        
        # TODO: Integrate with actual AI service
        # For now, create a mock AI response
        ai_response_content = self._generate_mock_ai_response(content, context)
        
        ai_message = AIMessage.objects.create(
            session=session,
            message_type='assistant',
            content=ai_response_content,
            confidence_score=0.85,
            concepts_referenced=self._extract_concepts(content)
        )
        
        # Update session
        session.total_messages += 2
        session.save()
        
        return Response({
            'user_message': AIMessageSerializer(user_message).data,
            'ai_response': AIMessageSerializer(ai_message).data
        })
    
    @action(detail=True, methods=['post'])
    def end_session(self, request, pk=None):
        """End an AI tutor session"""
        session = self.get_object()
        feedback_data = request.data.get('feedback', {})
        
        session.status = 'completed'
        session.ended_at = timezone.now()
        
        # Save feedback if provided
        if feedback_data:
            session.student_satisfaction = feedback_data.get('rating', None)
            session.helpfulness_rating = feedback_data.get('helpfulness', None)
        
        session.save()
        
        return Response({'message': 'Session ended successfully'})
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active sessions"""
        sessions = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)
    
    def _generate_mock_ai_response(self, user_input, context):
        """Generate a mock AI response until real AI integration"""
        responses = [
            "I understand you're working on this problem. Let me help you break it down step by step.",
            "That's a great question! Let me explain the concept and provide some guidance.",
            "I can see you're making progress. Here's a hint to help you move forward.",
            "Let's approach this differently. Consider the problem from this angle...",
            "Good effort! Here's some feedback on your approach and suggestions for improvement."
        ]
        
        import random
        return random.choice(responses) + f"\n\nBased on your input: '{user_input[:100]}...'"
    
    def _extract_concepts(self, content):
        """Extract programming concepts from user input"""
        concepts = []
        concept_keywords = {
            'loops': ['for', 'while', 'loop', 'iterate'],
            'functions': ['function', 'def', 'return', 'parameter'],
            'variables': ['variable', 'assign', 'var', 'let'],
            'conditionals': ['if', 'else', 'condition', 'boolean'],
            'data_structures': ['list', 'array', 'dict', 'object']
        }
        
        content_lower = content.lower()
        for concept, keywords in concept_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                concepts.append(concept)
        
        return concepts


class AIMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for AI messages"""
    serializer_class = AIMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return AIMessage.objects.filter(
            session__student=self.request.user
        ).order_by('-created_at')


class LearningPathRecommendationViewSet(viewsets.ModelViewSet):
    """API endpoints for learning path recommendations"""
    serializer_class = LearningPathRecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return LearningPathRecommendation.objects.filter(
            student=self.request.user,
            is_dismissed=False
        ).order_by('-priority', '-created_at')
    
    def perform_create(self, serializer):
        # Get default AI model for recommendations
        ai_model = AIModel.objects.filter(
            model_type='curriculum',
            is_active=True
        ).first()
        
        serializer.save(
            student=self.request.user,
            generated_by=ai_model
        )
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a learning recommendation"""
        recommendation = self.get_object()
        recommendation.is_accepted = True
        recommendation.accepted_at = timezone.now()
        recommendation.save()
        
        return Response({'message': 'Recommendation accepted'})
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Dismiss a learning recommendation"""
        recommendation = self.get_object()
        recommendation.is_dismissed = True
        recommendation.save()
        
        return Response({'message': 'Recommendation dismissed'})
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get recommendations by type"""
        recommendation_type = request.query_params.get('type', None)
        queryset = self.get_queryset()
        
        if recommendation_type:
            queryset = queryset.filter(recommendation_type=recommendation_type)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CodeAnalysisResultViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for code analysis results"""
    serializer_class = CodeAnalysisResultSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CodeAnalysisResult.objects.filter(
            submission__student=self.request.user
        ).order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def analyze_code(self, request):
        """Analyze submitted code"""
        code = request.data.get('code', '')
        language = request.data.get('language', 'python')
        analysis_type = request.data.get('analysis_type', 'best_practices')
        
        if not code.strip():
            return Response(
                {'error': 'Code cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Integrate with actual code analysis service
        # For now, return mock analysis
        mock_analysis = {
            'overall_score': 75,
            'issues_found': ['Consider using more descriptive variable names', 'Add comments for complex logic'],
            'suggestions': ['Break down long functions', 'Follow PEP 8 style guidelines'],
            'strengths': ['Good use of functions', 'Proper error handling'],
            'concepts_demonstrated': ['functions', 'error_handling'],
            'missing_concepts': ['unit_testing', 'documentation']
        }
        
        return Response(mock_analysis)


class PersonalizedQuizViewSet(viewsets.ModelViewSet):
    """API endpoints for personalized quizzes"""
    serializer_class = PersonalizedQuizSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PersonalizedQuiz.objects.filter(student=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        # Get default AI model for quiz generation
        ai_model = AIModel.objects.filter(
            model_type='quiz_generator',
            is_active=True
        ).first()
        
        serializer.save(
            student=self.request.user,
            generated_by=ai_model
        )
    
    @action(detail=True, methods=['post'])
    def submit_answers(self, request, pk=None):
        """Submit quiz answers"""
        quiz = self.get_object()
        answers = request.data.get('answers', [])
        
        if not answers:
            return Response(
                {'error': 'No answers provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Grade the quiz
        # For now, return mock results
        score = 85
        correct_answers = len(answers) * 0.85
        
        quiz.times_taken += 1
        quiz.average_score = (quiz.average_score + score) / quiz.times_taken
        quiz.save()
        
        return Response({
            'score': score,
            'correct_answers': int(correct_answers),
            'total_questions': len(answers),
            'feedback': 'Great job! You have a good understanding of the concepts.'
        })


class AITutorFeedbackViewSet(viewsets.ModelViewSet):
    """API endpoints for AI tutor feedback"""
    serializer_class = AITutorFeedbackSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return AITutorFeedback.objects.filter(
            session__student=self.request.user
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        session_id = self.request.data.get('session_id')
        if session_id:
            try:
                session = AITutorSession.objects.get(
                    id=session_id,
                    student=self.request.user
                )
                serializer.save(session=session)
            except AITutorSession.DoesNotExist:
                return Response(
                    {'error': 'Session not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )