# courses/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Sum
from datetime import timedelta

from .models import (
    CourseCategory, Course, Module, Lesson, Exercise,
    CourseEnrollment, LessonProgress, ExerciseSubmission
)

User = get_user_model()


# User serializer for course context
class CourseUserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'avatar', 'bio', 'role']


# Category Serializers
class CourseCategorySerializer(serializers.ModelSerializer):
    course_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 'color',
            'parent', 'order', 'is_active', 'course_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_course_count(self, obj):
        return obj.course_set.filter(status='published').count()


# Course Serializers
class CourseSerializer(serializers.ModelSerializer):
    instructor = CourseUserSerializer(read_only=True)
    category = CourseCategorySerializer(read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'category', 'instructor', 'difficulty_level', 'status',
            'thumbnail', 'preview_video', 'estimated_duration',
            'duration_formatted', 'total_lessons', 'total_exercises',
            'learning_objectives', 'skills_gained', 'tags',
            'programming_languages', 'is_free', 'price', 'premium_only',
            'average_rating', 'total_enrollments', 'total_reviews',
            'completion_rate', 'is_enrolled', 'user_progress',
            'created_at', 'published_at'
        ]
        read_only_fields = [
            'id', 'slug', 'total_lessons', 'total_exercises',
            'average_rating', 'total_enrollments', 'total_reviews',
            'completion_rate', 'created_at', 'published_at'
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
                    'exercises_completed': enrollment.exercises_completed,
                    'status': enrollment.status,
                    'last_accessed': enrollment.last_accessed,
                    'total_study_time': enrollment.total_study_time.total_seconds()
                }
            except CourseEnrollment.DoesNotExist:
                pass
        return None
    
    def get_duration_formatted(self, obj):
        """Format duration in human-readable format"""
        if obj.estimated_duration:
            total_seconds = obj.estimated_duration.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            
            if hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        return "0m"


class DetailedCourseSerializer(CourseSerializer):
    """Extended course serializer with modules and additional details"""
    modules = serializers.SerializerMethodField()
    prerequisites = CourseSerializer(many=True, read_only=True)
    co_instructors = CourseUserSerializer(many=True, read_only=True)
    recent_reviews = serializers.SerializerMethodField()
    enrollment_stats = serializers.SerializerMethodField()
    
    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + [
            'prerequisites', 'required_skills', 'co_instructors',
            'allow_enrollment', 'max_students', 'certificate_enabled',
            'discussion_enabled', 'modules', 'recent_reviews',
            'enrollment_stats'
        ]
    
    def get_modules(self, obj):
        modules = obj.modules.prefetch_related('lessons').order_by('order')
        return ModuleSerializer(modules, many=True, context=self.context).data
    
    def get_recent_reviews(self, obj):
        """Get recent course reviews"""
        # This would require a CourseReview model
        # For now, return empty list
        return []
    
    def get_enrollment_stats(self, obj):
        """Get enrollment statistics"""
        enrollments = obj.enrollments.all()
        
        return {
            'total_enrollments': enrollments.count(),
            'active_students': enrollments.filter(status='enrolled').count(),
            'completed_students': enrollments.filter(status='completed').count(),
            'completion_rate': float(obj.completion_rate),
            'average_progress': enrollments.aggregate(
                avg_progress=Avg('progress_percentage')
            )['avg_progress'] or 0
        }


# Module Serializers
class ModuleSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    exercises_count = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = [
            'id', 'title', 'description', 'order', 'is_required',
            'estimated_duration', 'duration_formatted', 'lessons_count',
            'exercises_count', 'user_progress', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_lessons_count(self, obj):
        return obj.lessons.count()
    
    def get_exercises_count(self, obj):
        return Exercise.objects.filter(lesson__module=obj).count()
    
    def get_duration_formatted(self, obj):
        if obj.estimated_duration:
            total_seconds = obj.estimated_duration.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        return "0m"
    
    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = obj.course.enrollments.get(student=request.user)
                total_lessons = obj.lessons.count()
                completed_lessons = LessonProgress.objects.filter(
                    enrollment=enrollment,
                    lesson__module=obj,
                    status='completed'
                ).count()
                
                return {
                    'total_lessons': total_lessons,
                    'completed_lessons': completed_lessons,
                    'progress_percentage': (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
                }
            except CourseEnrollment.DoesNotExist:
                pass
        return None


class DetailedModuleSerializer(ModuleSerializer):
    """Extended module serializer with lessons"""
    lessons = serializers.SerializerMethodField()
    
    class Meta(ModuleSerializer.Meta):
        fields = ModuleSerializer.Meta.fields + ['lessons']
    
    def get_lessons(self, obj):
        lessons = obj.lessons.order_by('order')
        return LessonSerializer(lessons, many=True, context=self.context).data


# Lesson Serializers
class LessonSerializer(serializers.ModelSerializer):
    module = ModuleSerializer(read_only=True)
    user_progress = serializers.SerializerMethodField()
    exercises_count = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()
    is_accessible = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'slug', 'lesson_type', 'description',
            'video_url', 'video_duration', 'order', 'estimated_duration',
            'duration_formatted', 'is_preview', 'is_required',
            'module', 'user_progress', 'exercises_count', 'is_accessible',
            'additional_resources', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = obj.module.course.enrollments.get(student=request.user)
                progress = enrollment.lesson_progress.get(lesson=obj)
                return {
                    'status': progress.status,
                    'progress_percentage': float(progress.progress_percentage),
                    'time_spent': progress.time_spent.total_seconds(),
                    'completed_at': progress.completed_at,
                    'bookmarked': progress.bookmarked,
                    'first_accessed': progress.first_accessed,
                    'last_accessed': progress.last_accessed
                }
            except (CourseEnrollment.DoesNotExist, LessonProgress.DoesNotExist):
                pass
        return None
    
    def get_exercises_count(self, obj):
        return obj.exercises.count()
    
    def get_duration_formatted(self, obj):
        if obj.estimated_duration:
            total_seconds = obj.estimated_duration.total_seconds()
            minutes = int(total_seconds // 60)
            return f"{minutes}m"
        return "0m"
    
    def get_is_accessible(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return obj.is_preview
        
        user = request.user
        
        # Always accessible for instructors and preview lessons
        if obj.module.course.instructor == user or obj.is_preview:
            return True
        
        # Check if user is enrolled
        if not obj.module.course.enrollments.filter(student=user).exists():
            return False
        
        # Check prerequisites
        if obj.prerequisites.exists():
            completed_prerequisites = LessonProgress.objects.filter(
                enrollment__student=user,
                lesson__in=obj.prerequisites.all(),
                status='completed'
            ).count()
            
            return completed_prerequisites == obj.prerequisites.count()
        
        return True


class DetailedLessonSerializer(LessonSerializer):
    """Extended lesson serializer with content and exercises"""
    content = serializers.CharField()  # Include full content for detailed view
    exercises = serializers.SerializerMethodField()
    next_lesson = serializers.SerializerMethodField()
    previous_lesson = serializers.SerializerMethodField()
    
    class Meta(LessonSerializer.Meta):
        fields = LessonSerializer.Meta.fields + [
            'content', 'exercises', 'next_lesson', 'previous_lesson'
        ]
    
    def get_exercises(self, obj):
        exercises = obj.exercises.order_by('order')
        return ExerciseSerializer(exercises, many=True, context=self.context).data
    
    def get_next_lesson(self, obj):
        try:
            next_lesson = Lesson.objects.filter(
                module=obj.module,
                order__gt=obj.order
            ).order_by('order').first()
            
            if next_lesson:
                return {
                    'id': next_lesson.id,
                    'title': next_lesson.title,
                    'slug': next_lesson.slug
                }
        except Lesson.DoesNotExist:
            pass
        return None
    
    def get_previous_lesson(self, obj):
        try:
            prev_lesson = Lesson.objects.filter(
                module=obj.module,
                order__lt=obj.order
            ).order_by('-order').first()
            
            if prev_lesson:
                return {
                    'id': prev_lesson.id,
                    'title': prev_lesson.title,
                    'slug': prev_lesson.slug
                }
        except Lesson.DoesNotExist:
            pass
        return None


# Exercise Serializers
class ExerciseSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer(read_only=True)
    user_submission = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()
    is_accessible = serializers.SerializerMethodField()
    
    class Meta:
        model = Exercise
        fields = [
            'id', 'title', 'exercise_type', 'difficulty', 'description',
            'programming_language', 'order', 'max_attempts', 'time_limit',
            'points', 'ai_hints_enabled', 'ai_explanation_enabled',
            'lesson', 'user_submission', 'success_rate', 'is_accessible',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'success_rate', 'created_at', 'updated_at']
    
    def get_user_submission(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            submission = obj.submissions.filter(
                student=request.user
            ).order_by('-submitted_at').first()
            
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
            return round((passed_submissions / total_submissions) * 100, 1)
        return 0
    
    def get_is_accessible(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        user = request.user
        course = obj.lesson.module.course
        
        # Always accessible for instructors
        if course.instructor == user:
            return True
        
        # Check if user is enrolled and lesson is accessible
        if not course.enrollments.filter(student=user).exists():
            return False
        
        # Check if lesson is completed or accessible
        lesson_serializer = LessonSerializer(obj.lesson, context=self.context)
        return lesson_serializer.get_is_accessible(obj.lesson)


class DetailedExerciseSerializer(ExerciseSerializer):
    """Extended exercise serializer with starter code and test cases"""
    starter_code = serializers.CharField()
    test_cases_preview = serializers.SerializerMethodField()
    submission_history = serializers.SerializerMethodField()
    hints_available = serializers.SerializerMethodField()
    
    class Meta(ExerciseSerializer.Meta):
        fields = ExerciseSerializer.Meta.fields + [
            'starter_code', 'test_cases_preview', 'submission_history',
            'hints_available', 'environment_config', 'hint_penalty'
        ]
    
    def get_test_cases_preview(self, obj):
        """Get preview of test cases (without expected outputs)"""
        if hasattr(obj, 'test_case_data') and obj.test_case_data:
            preview_cases = []
            for i, test_case in enumerate(obj.test_case_data[:3]):  # Show first 3
                preview_cases.append({
                    'name': test_case.get('name', f'Test Case {i+1}'),
                    'description': test_case.get('description', ''),
                    'input_example': test_case.get('input_data', '')
                })
            return preview_cases
        return []
    
    def get_submission_history(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            submissions = obj.submissions.filter(
                student=request.user
            ).order_by('-submitted_at')[:5]  # Last 5 submissions
            
            return [{
                'id': sub.id,
                'attempt_number': sub.attempt_number,
                'status': sub.status,
                'score': float(sub.score),
                'submitted_at': sub.submitted_at
            } for sub in submissions]
        return []
    
    def get_hints_available(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or not obj.ai_hints_enabled:
            return 0
        
        # Calculate hints used by user
        hints_used = obj.submissions.filter(
            student=request.user
        ).aggregate(total_hints=Sum('hints_used'))['total_hints'] or 0
        
        max_hints = 3  # Default max hints per exercise
        return max(0, max_hints - hints_used)


# Enrollment Serializers
class CourseEnrollmentSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    student = CourseUserSerializer(read_only=True)
    study_time_formatted = serializers.SerializerMethodField()
    progress_details = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'course', 'student', 'status', 'progress_percentage',
            'lessons_completed', 'exercises_completed', 'total_study_time',
            'study_time_formatted', 'progress_details', 'enrolled_at',
            'completed_at', 'last_accessed', 'certificate_issued',
            'certificate_url', 'enrollment_source'
        ]
        read_only_fields = [
            'id', 'progress_percentage', 'lessons_completed',
            'exercises_completed', 'total_study_time', 'enrolled_at'
        ]
    
    def get_study_time_formatted(self, obj):
        if obj.total_study_time:
            total_seconds = obj.total_study_time.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        return "0h 0m"
    
    def get_progress_details(self, obj):
        total_lessons = obj.course.total_lessons
        total_exercises = obj.course.total_exercises
        
        return {
            'lessons': {
                'completed': obj.lessons_completed,
                'total': total_lessons,
                'percentage': (obj.lessons_completed / total_lessons * 100) if total_lessons > 0 else 0
            },
            'exercises': {
                'completed': obj.exercises_completed,
                'total': total_exercises,
                'percentage': (obj.exercises_completed / total_exercises * 100) if total_exercises > 0 else 0
            }
        }


# Progress Serializers
class LessonProgressSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer(read_only=True)
    enrollment = serializers.StringRelatedField(read_only=True)
    time_spent_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'enrollment', 'lesson', 'status', 'progress_percentage',
            'time_spent', 'time_spent_formatted', 'first_accessed',
            'last_accessed', 'completed_at', 'notes', 'bookmarked'
        ]
        read_only_fields = ['id', 'first_accessed', 'last_accessed', 'completed_at']
    
    def get_time_spent_formatted(self, obj):
        if obj.time_spent:
            total_seconds = obj.time_spent.total_seconds()
            minutes = int(total_seconds // 60)
            return f"{minutes}m"
        return "0m"


# Submission Serializers
class ExerciseSubmissionSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)
    student = CourseUserSerializer(read_only=True)
    graded_by = CourseUserSerializer(read_only=True)
    test_results_summary = serializers.SerializerMethodField()
    time_taken_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = ExerciseSubmission
        fields = [
            'id', 'exercise', 'student', 'submitted_code', 'status',
            'score', 'execution_output', 'ai_feedback', 'instructor_feedback',
            'attempt_number', 'hints_used', 'time_taken', 'time_taken_formatted',
            'submitted_at', 'graded_at', 'graded_by', 'auto_graded',
            'test_results_summary'
        ]
        read_only_fields = [
            'id', 'student', 'status', 'score', 'execution_output',
            'ai_feedback', 'submitted_at', 'graded_at', 'graded_by'
        ]
    
    def get_test_results_summary(self, obj):
        # This would integrate with the code execution results
        # For now, return placeholder
        return {
            'total_tests': 0,
            'passed_tests': 0,
            'success_rate': 0
        }
    
    def get_time_taken_formatted(self, obj):
        if obj.time_taken:
            total_seconds = obj.time_taken.total_seconds()
            minutes = int(total_seconds // 60)
            seconds = int(total_seconds % 60)
            return f"{minutes}m {seconds}s"
        return "0m 0s"


class CreateExerciseSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for creating exercise submissions"""
    
    class Meta:
        model = ExerciseSubmission
        fields = ['submitted_code', 'hints_used', 'time_taken']
    
    def validate_submitted_code(self, value):
        if not value.strip():
            raise serializers.ValidationError("Submitted code cannot be empty")
        return value


# Statistics Serializers
class CourseStatsSerializer(serializers.Serializer):
    """Serializer for course statistics"""
    total_enrollments = serializers.IntegerField()
    active_students = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    average_rating = serializers.FloatField()
    average_progress = serializers.FloatField()
    total_study_time = serializers.DurationField()
    
    
class LearnerStatsSerializer(serializers.Serializer):
    """Serializer for learner statistics"""
    total_courses = serializers.IntegerField()
    completed_courses = serializers.IntegerField()
    in_progress_courses = serializers.IntegerField()
    total_lessons_completed = serializers.IntegerField()
    total_exercises_completed = serializers.IntegerField()
    total_study_time = serializers.DurationField()
    current_streak = serializers.IntegerField()
    average_score = serializers.FloatField()