# courses/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Course, CourseCategory, Module, Lesson, Exercise, 
    CourseEnrollment, LessonProgress, ExerciseSubmission
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for course context"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'avatar']
        read_only_fields = ['id', 'username', 'email', 'full_name']


class CourseCategorySerializer(serializers.ModelSerializer):
    """Serializer for course categories"""
    course_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 'color', 
            'parent', 'order', 'course_count'
        ]
        read_only_fields = ['id', 'slug']
    
    def get_course_count(self, obj):
        return obj.course_set.filter(status='published').count()


class ModuleSerializer(serializers.ModelSerializer):
    """Serializer for course modules"""
    lessons_count = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = [
            'id', 'title', 'description', 'order', 'is_required',
            'estimated_duration', 'lessons_count', 'user_progress'
        ]
        read_only_fields = ['id']
    
    def get_lessons_count(self, obj):
        return obj.lessons.count()
    
    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = obj.course.enrollments.get(student=request.user)
                total_lessons = obj.lessons.count()
                completed_lessons = enrollment.lesson_progress.filter(
                    lesson__module=obj,
                    status='completed'
                ).count()
                
                if total_lessons > 0:
                    progress_percentage = (completed_lessons / total_lessons) * 100
                else:
                    progress_percentage = 0
                
                return {
                    'total_lessons': total_lessons,
                    'completed_lessons': completed_lessons,
                    'progress_percentage': round(progress_percentage, 2)
                }
            except CourseEnrollment.DoesNotExist:
                pass
        return None


class LessonSerializer(serializers.ModelSerializer):
    """Serializer for lessons"""
    module = ModuleSerializer(read_only=True)
    user_progress = serializers.SerializerMethodField()
    exercises_count = serializers.SerializerMethodField()
    is_accessible = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'slug', 'lesson_type', 'description',
            'content', 'video_url', 'video_duration', 'order',
            'estimated_duration', 'is_preview', 'is_required',
            'module', 'user_progress', 'exercises_count', 'is_accessible',
            'additional_resources'
        ]
        read_only_fields = ['id', 'slug']
    
    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = obj.module.course.enrollments.get(student=request.user)
                progress = enrollment.lesson_progress.filter(lesson=obj).first()
                
                if progress:
                    return {
                        'status': progress.status,
                        'progress_percentage': float(progress.progress_percentage),
                        'time_spent': progress.time_spent.total_seconds(),
                        'completed_at': progress.completed_at,
                        'bookmarked': progress.bookmarked
                    }
            except CourseEnrollment.DoesNotExist:
                pass
        return None
    
    def get_exercises_count(self, obj):
        return obj.exercises.count()
    
    def get_is_accessible(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return obj.is_preview
        
        # Check if user is enrolled or if it's a preview lesson
        if obj.is_preview:
            return True
        
        try:
            enrollment = obj.module.course.enrollments.get(student=request.user)
            return True
        except CourseEnrollment.DoesNotExist:
            return False


class ExerciseSerializer(serializers.ModelSerializer):
    """Serializer for exercises"""
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
            return round((passed_submissions / total_submissions) * 100, 2)
        return 0


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for courses"""
    instructor = UserBasicSerializer(read_only=True)
    category = CourseCategorySerializer(read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    modules_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'category', 'instructor', 'difficulty_level', 'status',
            'thumbnail', 'preview_video', 'estimated_duration',
            'total_lessons', 'total_exercises', 'learning_objectives',
            'skills_gained', 'is_free', 'price', 'average_rating',
            'total_enrollments', 'completion_rate', 'is_enrolled',
            'user_progress', 'modules_count', 'created_at', 'published_at',
            'programming_languages', 'tags'
        ]
        read_only_fields = [
            'id', 'slug', 'total_lessons', 'total_exercises',
            'average_rating', 'total_enrollments', 'completion_rate',
            'created_at', 'published_at'
        ]
    
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.enrollments.filter(student=request.user, status='enrolled').exists()
        return False
    
    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = obj.enrollments.get(student=request.user)
                return {
                    'progress_percentage': float(enrollment.progress_percentage),
                    'lessons_completed': enrollment.lessons_completed,
                    'exercises_completed': enrollment.exercises_completed,
                    'status': enrollment.status,
                    'last_accessed': enrollment.last_accessed,
                    'total_study_time': enrollment.total_study_time.total_seconds()
                }
            except CourseEnrollment.DoesNotExist:
                pass
        return None
    
    def get_modules_count(self, obj):
        return obj.modules.count()


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for course enrollments"""
    course = CourseSerializer(read_only=True)
    student = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'course', 'student', 'status', 'progress_percentage',
            'lessons_completed', 'exercises_completed', 'total_study_time',
            'enrolled_at', 'completed_at', 'last_accessed', 'certificate_issued',
            'certificate_url', 'enrollment_source'
        ]
        read_only_fields = [
            'id', 'progress_percentage', 'lessons_completed',
            'exercises_completed', 'total_study_time', 'enrolled_at'
        ]


class LessonProgressSerializer(serializers.ModelSerializer):
    """Serializer for lesson progress"""
    lesson = LessonSerializer(read_only=True)
    enrollment = CourseEnrollmentSerializer(read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'lesson', 'enrollment', 'status', 'progress_percentage',
            'time_spent', 'first_accessed', 'last_accessed', 'completed_at',
            'notes', 'bookmarked'
        ]
        read_only_fields = ['id', 'first_accessed', 'last_accessed']


class ExerciseSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for exercise submissions"""
    exercise = ExerciseSerializer(read_only=True)
    student = UserBasicSerializer(read_only=True)
    test_results_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = ExerciseSubmission
        fields = [
            'id', 'exercise', 'student', 'submitted_code', 'status',
            'score', 'execution_output', 'ai_feedback', 'instructor_feedback',
            'attempt_number', 'hints_used', 'time_taken', 'submitted_at',
            'test_results_summary', 'auto_graded', 'graded_at'
        ]
        read_only_fields = [
            'id', 'student', 'status', 'score', 'execution_output',
            'ai_feedback', 'submitted_at', 'auto_graded', 'graded_at'
        ]
    
    def get_test_results_summary(self, obj):
        # TODO: Implement when test results are integrated
        return {
            'total_tests': 0,
            'passed_tests': 0,
            'success_rate': 0
        }


# Simplified serializers for nested relationships
class CourseListSerializer(serializers.ModelSerializer):
    """Simplified course serializer for lists"""
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'short_description', 'difficulty_level',
            'thumbnail', 'estimated_duration', 'is_free', 'price',
            'average_rating', 'total_enrollments', 'instructor_name',
            'category_name', 'is_enrolled', 'programming_languages'
        ]
    
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.enrollments.filter(student=request.user, status='enrolled').exists()
        return False


class ModuleListSerializer(serializers.ModelSerializer):
    """Simplified module serializer for lists"""
    lessons_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'order', 'lessons_count', 'estimated_duration']
    
    def get_lessons_count(self, obj):
        return obj.lessons.count()


class LessonListSerializer(serializers.ModelSerializer):
    """Simplified lesson serializer for lists"""
    module_title = serializers.CharField(source='module.title', read_only=True)
    is_completed = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'slug', 'lesson_type', 'order',
            'estimated_duration', 'is_preview', 'module_title', 'is_completed'
        ]
    
    def get_is_completed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = obj.module.course.enrollments.get(student=request.user)
                progress = enrollment.lesson_progress.filter(lesson=obj).first()
                return progress and progress.status == 'completed'
            except CourseEnrollment.DoesNotExist:
                pass
        return False