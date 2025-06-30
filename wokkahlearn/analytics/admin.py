from django.contrib import admin
from .models import (
    LearningAnalytics, StudySession, PerformanceMetric, LearningInsight,
    CourseAnalytics, InstructorAnalytics, PlatformAnalytics
)

@admin.register(LearningAnalytics)
class LearningAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_courses_completed', 'average_exercise_score', 'current_streak', 'learning_velocity')
    list_filter = ('learning_style', 'difficulty_preference')
    search_fields = ('user__username',)
    readonly_fields = ('last_updated',)

@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_type', 'course', 'duration', 'focus_score', 'started_at')
    list_filter = ('session_type', 'focus_score', 'satisfaction_level')
    search_fields = ('user__username', 'course__title')
    date_hierarchy = 'started_at'

@admin.register(CourseAnalytics)
class CourseAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('course', 'total_enrollments', 'completion_rate', 'average_rating', 'last_updated')
    list_filter = ('completion_rate', 'average_rating')
    search_fields = ('course__title',)