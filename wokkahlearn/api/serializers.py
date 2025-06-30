# api/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from courses.models import (
    Course, Module, Lesson, Exercise, CourseEnrollment, 
    LessonProgress, ExerciseSubmission, CourseCategory
)
from accounts.models import UserProfile, UserSkill, UserAchievement
from ai_tutor.models import AITutorSession, AIMessage, LearningPathRecommendation
from code_execution.models import CodeExecution, ExecutionEnvironment, TestResult
from analytics.models import LearningAnalytics, StudySession, PerformanceMetric

# Import collaboration serializers from collaboration app
from collaboration.serializers import (
    CollaborationRoomSerializer, RoomParticipantSerializer, 
    ChatMessageSerializer, SharedCodeSessionSerializer,
    HelpRequestSerializer, DetailedCollaborationRoomSerializer,
    CreateCollaborationRoomSerializer, CreateHelpRequestSerializer,
    CreateChatMessageSerializer
)

User = get_user_model()


# User and Profile Serializers
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'bio', 'avatar', 'github_username', 'linkedin_url', 
            'preferred_languages', 'skill_level', 'is_verified', 'is_premium',
            'timezone', 'language'
        ]
        read_only_fields = ['id', 'is_verified', 'is_premium']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'total_lessons_completed', 'total_exercises_completed',
            'current_streak', 'longest_streak', 'programming_skills',
            'weekly_goal_hours', 'ai_assistance_level', 'preferred_explanation_style',
            'public_profile', 'show_progress'
        ]


class UserSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSkill
        fields = [
            'id', 'skill_name', 'category', 'proficiency_level',
            'verified', 'evidence_count', 'last_assessed'
        ]


class UserAchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAchievement
        fields = [
            'id', 'achievement_id', 'achievement_type', 'title',
            'description', 'icon', 'earned_at', 'progress_data'
        ]


# Course Serializers
class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'color', 'parent']


class CourseSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)
    category = CourseCategorySerializer(read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'category', 'instructor', 'difficulty_level', 'status',
            'thumbnail', 'preview_video', 'estimated_duration',
            'total_lessons', 'total_exercises', 'learning_objectives',
            'skills_gained', 'is_free', 'price', 'average_rating',
            'total_enrollments', 'completion_rate', 'is_enrolled',
            'user_progress', 'created_at', 'published_at'
        ]
        read_only_fields = [
            'id', 'slug', 'total_lessons', 'total_exercises',
            'average_rating', 'total_enrollments', 'completion_rate'
        ]
    
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.enrollments.filter(student=request.user).exists()
        return False
    
    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = obj.enrollments.get(student=request.user)
                return {
                    'progress_percentage': float(enrollment.progress_percentage),
                    'lessons_completed': enrollment.lessons_completed,
                    'status': enrollment.status,
                    'last_accessed': enrollment.last_accessed
                }
            except CourseEnrollment.DoesNotExist:
                pass
        return None


class ModuleSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = [
            'id', 'title', 'description', 'order', 'is_required',
            'estimated_duration', 'lessons_count'
        ]
    
    def get_lessons_count(self, obj):
        return obj.lessons.count()


class LessonSerializer(serializers.ModelSerializer):
    module = ModuleSerializer(read_only=True)
    user_progress = serializers.SerializerMethodField()
    exercises_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'slug', 'lesson_type', 'description',
            'content', 'video_url', 'video_duration', 'order',
            'estimated_duration', 'is_preview', 'is_required',
            'module', 'user_progress', 'exercises_count',
            'additional_resources'
        ]
    
    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                # Get enrollment first
                enrollment = obj.module.course.enrollments.get(student=request.user)
                progress = enrollment.lesson_progress.get(lesson=obj)
                return {
                    'status': progress.status,
                    'progress_percentage': float(progress.progress_percentage),
                    'time_spent': progress.time_spent.total_seconds(),
                    'completed_at': progress.completed_at,
                    'bookmarked': progress.bookmarked
                }
            except (CourseEnrollment.DoesNotExist, LessonProgress.DoesNotExist):
                pass
        return None
    
    def get_exercises_count(self, obj):
        return obj.exercises.count()


class ExerciseSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer(read_only=True)
    user_submission = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Exercise
        fields = [
            'id', 'title', 'exercise_type', 'difficulty', 'description',
            'starter_code', 'programming_language', 'order', 'max_attempts',
            'time_limit', 'points', 'ai_hints_enabled', 'lesson',
            'user_submission', 'success_rate'
        ]
        read_only_fields = ['id', 'success_rate']
    
    def get_user_submission(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            submission = obj.submissions.filter(student=request.user).order_by('-submitted_at').first()
            if submission:
                return {
                    'id': submission.id,
                    'status': submission.status,
                    'score': float(submission.score),
                    'attempt_number': submission.attempt_number,
                    'submitted_at': submission.submitted_at,
                    'ai_feedback': submission.ai_feedback
                }
        return None
    
    def get_success_rate(self, obj):
        total_submissions = obj.submissions.count()
        if total_submissions > 0:
            passed_submissions = obj.submissions.filter(status='passed').count()
            return (passed_submissions / total_submissions) * 100
        return 0


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    student = UserSerializer(read_only=True)
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'course', 'student', 'status', 'progress_percentage',
            'lessons_completed', 'exercises_completed', 'total_study_time',
            'enrolled_at', 'completed_at', 'last_accessed', 'certificate_issued'
        ]
        read_only_fields = [
            'id', 'progress_percentage', 'lessons_completed',
            'exercises_completed', 'total_study_time', 'enrolled_at'
        ]


class ExerciseSubmissionSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)
    student = UserSerializer(read_only=True)
    test_results_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = ExerciseSubmission
        fields = [
            'id', 'exercise', 'student', 'submitted_code', 'status',
            'score', 'execution_output', 'ai_feedback', 'instructor_feedback',
            'attempt_number', 'hints_used', 'time_taken', 'submitted_at',
            'test_results_summary'
        ]
        read_only_fields = [
            'id', 'student', 'status', 'score', 'execution_output',
            'ai_feedback', 'submitted_at'
        ]
    
    def get_test_results_summary(self, obj):
        if hasattr(obj, 'execution'):
            test_results = obj.execution.test_results.all()
            total_tests = len(test_results)
            passed_tests = sum(1 for result in test_results if result.status == 'passed')
            
            return {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
            }
        return None


# AI Tutor Serializers
class AITutorSessionSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    latest_message = serializers.SerializerMethodField()
    
    class Meta:
        model = AITutorSession
        fields = [
            'id', 'student', 'session_type', 'status', 'title',
            'initial_query', 'total_messages', 'student_satisfaction',
            'started_at', 'ended_at', 'latest_message'
        ]
        read_only_fields = ['id', 'student', 'total_messages', 'started_at']
    
    def get_latest_message(self, obj):
        latest = obj.messages.order_by('-created_at').first()
        if latest:
            return {
                'content': latest.content[:100] + '...' if len(latest.content) > 100 else latest.content,
                'message_type': latest.message_type,
                'created_at': latest.created_at
            }
        return None


class AIMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMessage
        fields = [
            'id', 'message_type', 'content', 'code_language',
            'suggested_improvements', 'concepts_referenced',
            'confidence_score', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class LearningPathRecommendationSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    lesson = LessonSerializer(read_only=True)
    
    class Meta:
        model = LearningPathRecommendation
        fields = [
            'id', 'recommendation_type', 'priority', 'title',
            'description', 'reasoning', 'course', 'lesson',
            'confidence_score', 'estimated_completion_time',
            'is_accepted', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at']


# Code Execution Serializers
class ExecutionEnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutionEnvironment
        fields = [
            'id', 'name', 'language', 'version', 'file_extension',
            'default_timeout', 'max_memory', 'supports_input',
            'supports_graphics', 'installed_packages', 'is_default'
        ]


class CodeExecutionSerializer(serializers.ModelSerializer):
    environment = ExecutionEnvironmentSerializer(read_only=True)
    test_results_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeExecution
        fields = [
            'id', 'environment', 'execution_type', 'status',
            'source_code', 'stdin_input', 'stdout_output', 'stderr_output',
            'exit_code', 'execution_time', 'memory_used', 'created_at',
            'started_at', 'completed_at', 'test_results_summary'
        ]
        read_only_fields = [
            'id', 'status', 'stdout_output', 'stderr_output',
            'exit_code', 'execution_time', 'memory_used', 'created_at',
            'started_at', 'completed_at'
        ]
    
    def get_test_results_summary(self, obj):
        if hasattr(obj, 'test_results'):
            test_results = obj.test_results.all()
            total = test_results.count()
            passed = test_results.filter(status='passed').count()
            
            return {
                'total_tests': total,
                'passed_tests': passed,
                'success_rate': (passed / total * 100) if total > 0 else 0
            }
        return None


# Analytics Serializers
class LearningAnalyticsSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    total_study_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningAnalytics
        fields = [
            'user', 'total_study_hours', 'total_courses_enrolled',
            'total_courses_completed', 'total_lessons_completed',
            'average_exercise_score', 'success_rate', 'current_streak',
            'longest_streak', 'learning_velocity', 'learning_style',
            'at_risk_score', 'last_updated'
        ]
        read_only_fields = ['user', 'last_updated']
    
    def get_total_study_hours(self, obj):
        return obj.total_study_time.total_seconds() / 3600


class StudySessionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    duration_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = StudySession
        fields = [
            'id', 'user', 'session_type', 'course', 'duration_hours',
            'focus_score', 'productivity_score', 'exercises_attempted',
            'exercises_completed', 'average_score', 'satisfaction_level',
            'started_at', 'ended_at'
        ]
        read_only_fields = ['id', 'user']
    
    def get_duration_hours(self, obj):
        return obj.duration.total_seconds() / 3600


class PerformanceMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceMetric
        fields = [
            'id', 'metric_type', 'granularity', 'value',
            'previous_value', 'change_percentage', 'period_start',
            'period_end', 'created_at'
        ]