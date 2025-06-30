# analytics/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    LearningAnalytics, StudySession, PerformanceMetric, LearningInsight,
    CourseAnalytics, InstructorAnalytics, PlatformAnalytics
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for analytics context"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name']
        read_only_fields = ['id', 'username', 'full_name']


class LearningAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for learning analytics"""
    user = UserBasicSerializer(read_only=True)
    total_study_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningAnalytics
        fields = [
            'user', 'total_study_hours', 'total_courses_enrolled',
            'total_courses_completed', 'total_lessons_completed',
            'total_exercises_completed', 'total_projects_completed',
            'average_exercise_score', 'average_completion_time',
            'success_rate', 'preferred_study_times', 'most_productive_days',
            'learning_velocity', 'current_streak', 'longest_streak',
            'forum_posts', 'help_requests_made', 'help_provided',
            'skill_progression', 'strengths', 'areas_for_improvement',
            'learning_style', 'difficulty_preference', 'predicted_completion_date',
            'predicted_success_probability', 'at_risk_score', 'last_updated'
        ]
        read_only_fields = ['user', 'last_updated']
    
    def get_total_study_hours(self, obj):
        return obj.total_study_time.total_seconds() / 3600


class StudySessionSerializer(serializers.ModelSerializer):
    """Serializer for study sessions"""
    user = UserBasicSerializer(read_only=True)
    course = serializers.SerializerMethodField()
    lesson = serializers.SerializerMethodField()
    duration_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = StudySession
        fields = [
            'id', 'user', 'session_type', 'course', 'lesson', 'exercise',
            'duration_hours', 'focus_score', 'productivity_score',
            'actions_performed', 'concepts_studied', 'skills_practiced',
            'exercises_attempted', 'exercises_completed', 'average_score',
            'frustration_level', 'satisfaction_level', 'started_at', 'ended_at'
        ]
        read_only_fields = ['id', 'user']
    
    def get_course(self, obj):
        if obj.course:
            return {
                'id': obj.course.id,
                'title': obj.course.title,
                'slug': obj.course.slug
            }
        return None
    
    def get_lesson(self, obj):
        if obj.lesson:
            return {
                'id': obj.lesson.id,
                'title': obj.lesson.title,
                'slug': obj.lesson.slug
            }
        return None
    
    def get_duration_hours(self, obj):
        return obj.duration.total_seconds() / 3600


class PerformanceMetricSerializer(serializers.ModelSerializer):
    """Serializer for performance metrics"""
    user = UserBasicSerializer(read_only=True)
    course = serializers.SerializerMethodField()
    
    class Meta:
        model = PerformanceMetric
        fields = [
            'id', 'user', 'metric_type', 'granularity', 'value',
            'previous_value', 'change_percentage', 'course', 'skill',
            'period_start', 'period_end', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']
    
    def get_course(self, obj):
        if obj.course:
            return {
                'id': obj.course.id,
                'title': obj.course.title
            }
        return None


class LearningInsightSerializer(serializers.ModelSerializer):
    """Serializer for learning insights"""
    user = UserBasicSerializer(read_only=True)
    course = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningInsight
        fields = [
            'id', 'user', 'insight_type', 'priority', 'title', 'message',
            'detailed_analysis', 'supporting_data', 'confidence_score',
            'course', 'skill', 'recommended_actions', 'is_read',
            'is_acted_upon', 'generated_by', 'generation_context',
            'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'user', 'generated_by', 'created_at']
    
    def get_course(self, obj):
        if obj.course:
            return {
                'id': obj.course.id,
                'title': obj.course.title
            }
        return None


class CourseAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for course analytics"""
    course = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseAnalytics
        fields = [
            'course', 'total_enrollments', 'active_students', 'completion_rate',
            'dropout_rate', 'average_grade', 'average_completion_time',
            'exercise_success_rate', 'average_study_time_per_student',
            'forum_activity_score', 'collaboration_rate', 'most_difficult_lessons',
            'most_helpful_lessons', 'bottleneck_exercises', 'average_rating',
            'satisfaction_score', 'enrollment_trend', 'completion_trend',
            'engagement_trend', 'last_updated'
        ]
        read_only_fields = ['last_updated']
    
    def get_course(self, obj):
        return {
            'id': obj.course.id,
            'title': obj.course.title,
            'slug': obj.course.slug,
            'difficulty_level': obj.course.difficulty_level,
            'instructor': obj.course.instructor.get_full_name()
        }


class InstructorAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for instructor analytics"""
    instructor = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = InstructorAnalytics
        fields = [
            'instructor', 'total_courses_taught', 'total_students_taught',
            'average_course_rating', 'student_satisfaction_score',
            'lessons_created', 'exercises_created', 'content_quality_score',
            'average_student_completion_rate', 'average_student_performance',
            'student_success_rate', 'response_time_to_questions',
            'forum_participation', 'office_hours_utilization',
            'skills_taught', 'certifications', 'professional_growth_score',
            'last_updated'
        ]
        read_only_fields = ['instructor', 'last_updated']


class PlatformAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for platform analytics"""
    
    class Meta:
        model = PlatformAnalytics
        fields = [
            'date', 'total_users', 'active_users_daily', 'new_registrations',
            'user_retention_rate', 'total_courses', 'courses_published',
            'total_enrollments', 'course_completion_rate', 'total_study_time',
            'exercises_completed', 'projects_completed', 'certificates_issued',
            'collaboration_sessions', 'ai_interactions', 'help_requests',
            'forum_posts', 'average_course_rating', 'student_satisfaction',
            'platform_uptime', 'average_response_time', 'code_execution_success_rate',
            'ai_accuracy_score', 'created_at'
        ]
        read_only_fields = ['date', 'created_at']


# Simplified serializers for dashboard and summaries
class AnalyticsSummarySerializer(serializers.ModelSerializer):
    """Simplified analytics for dashboard"""
    total_study_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningAnalytics
        fields = [
            'total_study_hours', 'total_courses_completed',
            'current_streak', 'average_exercise_score',
            'learning_velocity', 'at_risk_score'
        ]
    
    def get_total_study_hours(self, obj):
        return obj.total_study_time.total_seconds() / 3600


class StudySessionSummarySerializer(serializers.ModelSerializer):
    """Simplified study session for lists"""
    duration_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = StudySession
        fields = [
            'id', 'session_type', 'duration_minutes', 'focus_score',
            'started_at', 'ended_at'
        ]
    
    def get_duration_minutes(self, obj):
        return obj.duration.total_seconds() / 60


class MetricTrendSerializer(serializers.ModelSerializer):
    """Simplified metric for trend analysis"""
    
    class Meta:
        model = PerformanceMetric
        fields = [
            'metric_type', 'value', 'change_percentage',
            'period_start', 'period_end'
        ]


class InsightSummarySerializer(serializers.ModelSerializer):
    """Simplified insight for notifications"""
    
    class Meta:
        model = LearningInsight
        fields = [
            'id', 'insight_type', 'priority', 'title',
            'confidence_score', 'is_read', 'created_at'
        ]