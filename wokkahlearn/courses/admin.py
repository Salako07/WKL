from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CourseCategory, Course, Module, Lesson, Exercise, 
    CourseEnrollment, LessonProgress, ExerciseSubmission
)

@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'order', 'is_active', 'course_count')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')
    
    def course_count(self, obj):
        return obj.course_set.count()
    course_count.short_description = 'Courses'

class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0
    fields = ('title', 'order', 'is_required', 'estimated_duration')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'difficulty_level', 'status', 'total_enrollments', 'average_rating')
    list_filter = ('status', 'difficulty_level', 'category', 'is_free', 'premium_only')
    search_fields = ('title', 'description', 'instructor__username')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('co_instructors', 'prerequisites')
    inlines = [ModuleInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'short_description', 'category')
        }),
        ('Content', {
            'fields': ('instructor', 'co_instructors', 'difficulty_level', 'status')
        }),
        ('Media', {
            'fields': ('thumbnail', 'preview_video')
        }),
        ('Structure', {
            'fields': ('estimated_duration', 'learning_objectives', 'skills_gained', 'tags')
        }),
        ('Prerequisites', {
            'fields': ('prerequisites', 'required_skills', 'programming_languages')
        }),
        ('Pricing', {
            'fields': ('is_free', 'price', 'premium_only')
        }),
        ('Settings', {
            'fields': ('allow_enrollment', 'max_students', 'certificate_enabled', 'discussion_enabled')
        }),
    )

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ('title', 'lesson_type', 'order', 'is_required', 'estimated_duration')

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'is_required', 'lesson_count')
    list_filter = ('is_required', 'course__category')
    search_fields = ('title', 'description', 'course__title')
    inlines = [LessonInline]
    
    def lesson_count(self, obj):
        return obj.lessons.count()
    lesson_count.short_description = 'Lessons'

class ExerciseInline(admin.TabularInline):
    model = Exercise
    extra = 0
    fields = ('title', 'exercise_type', 'difficulty', 'order', 'points')

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'lesson_type', 'order', 'is_required', 'estimated_duration')
    list_filter = ('lesson_type', 'is_required', 'is_preview', 'module__course__category')
    search_fields = ('title', 'description', 'module__title')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ExerciseInline]

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'exercise_type', 'difficulty', 'programming_language', 'points')
    list_filter = ('exercise_type', 'difficulty', 'programming_language', 'ai_hints_enabled')
    search_fields = ('title', 'description', 'lesson__title')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'lesson', 'exercise_type', 'difficulty', 'description')
        }),
        ('Code', {
            'fields': ('starter_code', 'solution_code', 'programming_language', 'environment_config')
        }),
        ('Testing', {
            'fields': ('test_cases', 'validation_code')
        }),
        ('Settings', {
            'fields': ('order', 'max_attempts', 'time_limit', 'points')
        }),
        ('AI Features', {
            'fields': ('ai_hints_enabled', 'ai_explanation_enabled', 'hint_penalty')
        }),
        ('Collaboration', {
            'fields': ('allow_collaboration', 'peer_review_enabled')
        }),
    )

@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'progress_percentage', 'enrolled_at', 'completed_at')
    list_filter = ('status', 'enrollment_source', 'certificate_issued')
    search_fields = ('student__username', 'course__title')
    date_hierarchy = 'enrolled_at'

@admin.register(ExerciseSubmission)
class ExerciseSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'exercise', 'status', 'score', 'attempt_number', 'submitted_at')
    list_filter = ('status', 'auto_graded', 'exercise__programming_language')
    search_fields = ('student__username', 'exercise__title')
    date_hierarchy = 'submitted_at'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return ('student', 'exercise', 'submitted_code', 'attempt_number', 'submitted_at')
        return ()