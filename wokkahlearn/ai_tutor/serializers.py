# ai_tutor/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    AIModel, AITutorSession, AIMessage, LearningPathRecommendation,
    CodeAnalysisResult, PersonalizedQuiz, AITutorFeedback
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for AI tutor context"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'avatar']
        read_only_fields = ['id', 'username', 'full_name']


class AIModelSerializer(serializers.ModelSerializer):
    """Serializer for AI models"""
    
    class Meta:
        model = AIModel
        fields = [
            'id', 'name', 'model_type', 'provider', 'model_id',
            'max_tokens', 'temperature', 'top_p', 'supports_code',
            'supports_streaming', 'supports_function_calling',
            'programming_languages', 'cost_per_token', 'rate_limit_per_minute',
            'average_response_time', 'is_active', 'is_default'
        ]
        read_only_fields = ['id', 'average_response_time']


class AIMessageSerializer(serializers.ModelSerializer):
    """Serializer for AI messages"""
    
    class Meta:
        model = AIMessage
        fields = [
            'id', 'message_type', 'content', 'code_language',
            'code_analysis', 'suggested_improvements', 'concepts_referenced',
            'difficulty_level', 'requires_human_review', 'confidence_score',
            'tokens_used', 'response_time', 'created_at'
        ]
        read_only_fields = ['id', 'tokens_used', 'response_time', 'created_at']


class AITutorSessionSerializer(serializers.ModelSerializer):
    """Serializer for AI tutor sessions"""
    student = UserBasicSerializer(read_only=True)
    ai_model = AIModelSerializer(read_only=True)
    latest_message = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = AITutorSession
        fields = [
            'id', 'student', 'ai_model', 'session_type', 'status', 'title',
            'initial_query', 'context_data', 'total_messages', 'total_tokens_used',
            'total_cost', 'student_satisfaction', 'helpfulness_rating',
            'started_at', 'ended_at', 'last_activity', 'latest_message', 'duration'
        ]
        read_only_fields = [
            'id', 'student', 'total_messages', 'total_tokens_used',
            'total_cost', 'started_at', 'last_activity'
        ]
    
    def get_latest_message(self, obj):
        latest = obj.messages.order_by('-created_at').first()
        if latest:
            return {
                'content': latest.content[:100] + '...' if len(latest.content) > 100 else latest.content,
                'message_type': latest.message_type,
                'created_at': latest.created_at
            }
        return None
    
    def get_duration(self, obj):
        if obj.ended_at and obj.started_at:
            duration = obj.ended_at - obj.started_at
            return duration.total_seconds()
        return None


class LearningPathRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for learning path recommendations"""
    student = UserBasicSerializer(read_only=True)
    generated_by = AIModelSerializer(read_only=True)
    course = serializers.SerializerMethodField()
    lesson = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningPathRecommendation
        fields = [
            'id', 'student', 'recommendation_type', 'priority', 'title',
            'description', 'reasoning', 'course', 'lesson', 'external_resource',
            'confidence_score', 'estimated_completion_time', 'skill_level_required',
            'is_accepted', 'is_dismissed', 'viewed_at', 'accepted_at',
            'completed_at', 'generated_by', 'generation_context',
            'created_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'student', 'generated_by', 'viewed_at', 'accepted_at',
            'completed_at', 'created_at'
        ]
    
    def get_course(self, obj):
        if obj.course:
            return {
                'id': obj.course.id,
                'title': obj.course.title,
                'slug': obj.course.slug,
                'difficulty_level': obj.course.difficulty_level
            }
        return None
    
    def get_lesson(self, obj):
        if obj.lesson:
            return {
                'id': obj.lesson.id,
                'title': obj.lesson.title,
                'slug': obj.lesson.slug,
                'lesson_type': obj.lesson.lesson_type
            }
        return None


class CodeAnalysisResultSerializer(serializers.ModelSerializer):
    """Serializer for code analysis results"""
    ai_model = AIModelSerializer(read_only=True)
    submission = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeAnalysisResult
        fields = [
            'id', 'submission', 'analysis_type', 'ai_model', 'overall_score',
            'issues_found', 'suggestions', 'strengths', 'summary',
            'detailed_feedback', 'improvement_suggestions', 'complexity_score',
            'readability_score', 'maintainability_score', 'concepts_demonstrated',
            'missing_concepts', 'next_learning_steps', 'analysis_duration',
            'tokens_used', 'confidence_score', 'created_at'
        ]
        read_only_fields = [
            'id', 'analysis_duration', 'tokens_used', 'created_at'
        ]
    
    def get_submission(self, obj):
        if obj.submission:
            return {
                'id': obj.submission.id,
                'exercise_title': obj.submission.exercise.title,
                'submitted_at': obj.submission.submitted_at
            }
        return None


class PersonalizedQuizSerializer(serializers.ModelSerializer):
    """Serializer for personalized quizzes"""
    student = UserBasicSerializer(read_only=True)
    generated_by = AIModelSerializer(read_only=True)
    
    class Meta:
        model = PersonalizedQuiz
        fields = [
            'id', 'student', 'quiz_type', 'title', 'description',
            'questions', 'correct_answers', 'explanations', 'difficulty_level',
            'estimated_duration', 'topics_covered', 'based_on_weaknesses',
            'adaptation_reason', 'generated_by', 'generation_prompt',
            'generation_context', 'times_taken', 'average_score',
            'created_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'student', 'generated_by', 'times_taken',
            'average_score', 'created_at'
        ]


class AITutorFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for AI tutor feedback"""
    session = AITutorSessionSerializer(read_only=True)
    
    class Meta:
        model = AITutorFeedback
        fields = [
            'id', 'session', 'overall_rating', 'helpfulness', 'accuracy',
            'clarity', 'response_time', 'what_worked_well', 'what_could_improve',
            'additional_comments', 'problem_solved', 'would_recommend',
            'needs_human_tutor', 'suggested_improvements', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# Simplified serializers for quick responses
class AISessionSummarySerializer(serializers.ModelSerializer):
    """Simplified AI session serializer for summaries"""
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = AITutorSession
        fields = [
            'id', 'session_type', 'status', 'title', 'total_messages',
            'student_satisfaction', 'started_at', 'ended_at', 'duration'
        ]
    
    def get_duration(self, obj):
        if obj.ended_at and obj.started_at:
            duration = obj.ended_at - obj.started_at
            return duration.total_seconds()
        return None


class RecommendationSummarySerializer(serializers.ModelSerializer):
    """Simplified recommendation serializer for summaries"""
    
    class Meta:
        model = LearningPathRecommendation
        fields = [
            'id', 'recommendation_type', 'priority', 'title',
            'confidence_score', 'is_accepted', 'created_at'
        ]