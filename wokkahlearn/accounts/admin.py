from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Organization, UserProfile, UserSkill, UserAchievement

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'full_name', 'role', 'is_verified', 'is_premium', 'last_activity')
    list_filter = ('role', 'is_verified', 'is_premium', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile', {
            'fields': ('role', 'bio', 'avatar', 'github_username', 'linkedin_url', 'website_url')
        }),
        ('Learning', {
            'fields': ('preferred_languages', 'skill_level', 'last_activity', 'total_study_time')
        }),
        ('Status', {
            'fields': ('is_verified', 'verification_date', 'is_premium', 'premium_expires')
        }),
        ('Organization', {
            'fields': ('organization',)
        }),
        ('Preferences', {
            'fields': ('timezone', 'language', 'email_notifications', 'marketing_emails')
        }),
    )
    
    def full_name(self, obj):
        return obj.get_full_name() or obj.username
    full_name.short_description = 'Full Name'

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'org_type', 'subscription_tier', 'is_active', 'user_count')
    list_filter = ('org_type', 'subscription_tier', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    def user_count(self, obj):
        return obj.user_set.count()
    user_count.short_description = 'Users'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_streak', 'total_lessons_completed', 'total_exercises_completed')
    list_filter = ('ai_assistance_level', 'preferred_explanation_style', 'public_profile')
    search_fields = ('user__username', 'user__email')

@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill_name', 'category', 'proficiency_level', 'verified', 'last_assessed')
    list_filter = ('category', 'verified', 'proficiency_level')
    search_fields = ('user__username', 'skill_name')

@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'achievement_type', 'earned_at')
    list_filter = ('achievement_type', 'earned_at')
    search_fields = ('user__username', 'title')