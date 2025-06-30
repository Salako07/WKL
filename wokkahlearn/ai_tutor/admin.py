from django.contrib import admin
from .models import (
    AIModel, AITutorSession, AIMessage, LearningPathRecommendation,
    CodeAnalysisResult, PersonalizedQuiz, AITutorFeedback, AIModelUsageStats
)

@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_type', 'provider', 'is_active', 'is_default', 'average_response_time')
    list_filter = ('model_type', 'provider', 'is_active', 'is_default', 'supports_code')
    search_fields = ('name', 'model_id')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'model_type', 'provider', 'model_id')
        }),
        ('Configuration', {
            'fields': ('max_tokens', 'temperature', 'top_p')
        }),
        ('Capabilities', {
            'fields': ('supports_code', 'supports_streaming', 'supports_function_calling', 'programming_languages')
        }),
        ('Performance', {
            'fields': ('cost_per_token', 'rate_limit_per_minute', 'average_response_time')
        }),
        ('Status', {
            'fields': ('is_active', 'is_default')
        }),
    )

@admin.register(AITutorSession)
class AITutorSessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'session_type', 'status', 'total_messages', 'student_satisfaction', 'started_at')
    list_filter = ('session_type', 'status', 'ai_model', 'student_satisfaction')
    search_fields = ('student__username', 'title', 'initial_query')
    date_hierarchy = 'started_at'

@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'message_type', 'content_preview', 'confidence_score', 'created_at')
    list_filter = ('message_type', 'code_language', 'requires_human_review')
    search_fields = ('session__student__username', 'content')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'

@admin.register(LearningPathRecommendation)
class LearningPathRecommendationAdmin(admin.ModelAdmin):
    list_display = ('student', 'recommendation_type', 'priority', 'title', 'confidence_score', 'is_accepted')
    list_filter = ('recommendation_type', 'priority', 'is_accepted', 'is_dismissed')
    search_fields = ('student__username', 'title', 'description')