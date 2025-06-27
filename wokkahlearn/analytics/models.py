# analytics/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Count, Sum
import uuid
import json
from datetime import datetime, timedelta

User = get_user_model()


class LearningAnalytics(models.Model):
    """Comprehensive learning analytics for students"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='learning_analytics')
    
    # Overall progress
    total_study_time = models.DurationField(default=timedelta(0))
    total_courses_enrolled = models.PositiveIntegerField(default=0)
    total_courses_completed = models.PositiveIntegerField(default=0)
    total_lessons_completed = models.PositiveIntegerField(default=0)
    total_exercises_completed = models.PositiveIntegerField(default=0)
    total_projects_completed = models.PositiveIntegerField(default=0)
    
    # Performance metrics
    average_exercise_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    average_completion_time = models.DurationField(default=timedelta(0))
    success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Learning patterns
    preferred_study_times = models.JSONField(default=list)  # Hours of day when most active
    most_productive_days = models.JSONField(default=list)  # Days of week when most productive
    learning_velocity = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # Lessons per week
    
    # Engagement metrics
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    forum_posts = models.PositiveIntegerField(default=0)
    help_requests_made = models.PositiveIntegerField(default=0)
    help_provided = models.PositiveIntegerField(default=0)
    
    # Skill development
    skill_progression = models.JSONField(default=dict)  # {"python": {"start": 20, "current": 75}}
    strengths = models.JSONField(default=list)
    areas_for_improvement = models.JSONField(default=list)
    
    # AI insights
    learning_style = models.CharField(
        max_length=20,
        choices=[
            ('visual', 'Visual'),
            ('auditory', 'Auditory'),
            ('kinesthetic', 'Kinesthetic'),
            ('reading', 'Reading/Writing'),
            ('mixed', 'Mixed')
        ],
        default='mixed'
    )
    difficulty_preference = models.CharField(
        max_length=20,
        choices=[
            ('gradual', 'Gradual Progression'),
            ('challenging', 'Challenging'),
            ('mixed', 'Mixed Difficulty')
        ],
        default='gradual'
    )
    
    # Predictions
    predicted_completion_date = models.DateField(null=True, blank=True)
    predicted_success_probability = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    at_risk_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0,
        help_text="Risk of dropping out (0-100)"
    )
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Learning Analytics')
        verbose_name_plural = _('Learning Analytics')
    
    def __str__(self):
        return f"Analytics for {self.user.get_full_name()}"
    
    def update_analytics(self):
        """Update analytics based on recent activity"""
        from django.utils import timezone
        from django.db.models import Avg, Sum
        
        # Update basic counts
        enrollments = self.user.enrollments.all()
        self.total_courses_enrolled = enrollments.count()
        self.total_courses_completed = enrollments.filter(
            status='completed'
        ).count()
        
        # Update exercise performance
        submissions = self.user.exercise_submissions.all()
        if submissions.exists():
            self.average_exercise_score = submissions.aggregate(
                avg_score=Avg('score')
            )['avg_score'] or 0.0
        
        # Update success rate
        if submissions.exists():
            passed_submissions = submissions.filter(status='passed').count()
            self.success_rate = (passed_submissions / submissions.count()) * 100
        
        # Update learning velocity (lessons per week in last 4 weeks)
        four_weeks_ago = timezone.now() - timedelta(weeks=4)
        recent_progress = self.user.lesson_progress.filter(
            completed_at__gte=four_weeks_ago,
            status='completed'
        ).count()
        self.learning_velocity = recent_progress / 4.0
        
        self.save()


class StudySession(models.Model):
    """Individual study sessions"""
    
    class SessionType(models.TextChoices):
        LESSON = 'lesson', _('Lesson Study')
        EXERCISE = 'exercise', _('Exercise Practice')
        PROJECT = 'project', _('Project Work')
        REVIEW = 'review', _('Review Session')
        COLLABORATION = 'collaboration', _('Collaborative Study')
        SELF_STUDY = 'self_study', _('Self Study')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_sessions')
    session_type = models.CharField(max_length=20, choices=SessionType.choices)
    
    # Session context
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, null=True, blank=True)
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, null=True, blank=True)
    exercise = models.ForeignKey('courses.Exercise', on_delete=models.CASCADE, null=True, blank=True)
    
    # Session metrics
    duration = models.DurationField()
    focus_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Focus level during session (0-100)"
    )
    productivity_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Productivity level (0-100)"
    )
    
    # Activity tracking
    actions_performed = models.JSONField(default=list)  # List of actions taken
    concepts_studied = models.JSONField(default=list)  # Concepts covered
    skills_practiced = models.JSONField(default=list)  # Skills practiced
    
    # Performance
    exercises_attempted = models.PositiveIntegerField(default=0)
    exercises_completed = models.PositiveIntegerField(default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Session quality
    frustration_level = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    satisfaction_level = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    
    # Timestamps
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Study Session')
        verbose_name_plural = _('Study Sessions')
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_session_type_display()} ({self.duration})"


class PerformanceMetric(models.Model):
    """Track performance metrics over time"""
    
    class MetricType(models.TextChoices):
        COMPLETION_RATE = 'completion_rate', _('Completion Rate')
        AVERAGE_SCORE = 'average_score', _('Average Score')
        STUDY_TIME = 'study_time', _('Study Time')
        EXERCISE_ACCURACY = 'exercise_accuracy', _('Exercise Accuracy')
        LEARNING_VELOCITY = 'learning_velocity', _('Learning Velocity')
        ENGAGEMENT_SCORE = 'engagement_score', _('Engagement Score')
        SKILL_LEVEL = 'skill_level', _('Skill Level')
    
    class Granularity(models.TextChoices):
        DAILY = 'daily', _('Daily')
        WEEKLY = 'weekly', _('Weekly')
        MONTHLY = 'monthly', _('Monthly')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance_metrics')
    metric_type = models.CharField(max_length=20, choices=MetricType.choices)
    granularity = models.CharField(max_length=10, choices=Granularity.choices)
    
    # Metric value
    value = models.DecimalField(max_digits=10, decimal_places=2)
    previous_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    change_percentage = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    
    # Context
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, null=True, blank=True)
    skill = models.CharField(max_length=100, blank=True)
    
    # Time period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Metadata
    metadata = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Performance Metric')
        verbose_name_plural = _('Performance Metrics')
        unique_together = ['user', 'metric_type', 'granularity', 'period_start', 'course', 'skill']
        ordering = ['-period_start']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_metric_type_display()}: {self.value}"


class LearningInsight(models.Model):
    """AI-generated learning insights and recommendations"""
    
    class InsightType(models.TextChoices):
        PERFORMANCE = 'performance', _('Performance Insight')
        BEHAVIOR = 'behavior', _('Learning Behavior')
        PREDICTION = 'prediction', _('Predictive Insight')
        RECOMMENDATION = 'recommendation', _('Recommendation')
        WARNING = 'warning', _('Warning/Alert')
        ACHIEVEMENT = 'achievement', _('Achievement Recognition')
    
    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_insights')
    insight_type = models.CharField(max_length=20, choices=InsightType.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    
    # Insight content
    title = models.CharField(max_length=200)
    message = models.TextField()
    detailed_analysis = models.TextField(blank=True)
    
    # Supporting data
    supporting_data = models.JSONField(default=dict)
    confidence_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Context
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, null=True, blank=True)
    skill = models.CharField(max_length=100, blank=True)
    
    # Action items
    recommended_actions = models.JSONField(default=list)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_acted_upon = models.BooleanField(default=False)
    
    # AI generation info
    generated_by = models.CharField(max_length=100, default='analytics_engine')
    generation_context = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Learning Insight')
        verbose_name_plural = _('Learning Insights')
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"Insight for {self.user.username}: {self.title}"


class CourseAnalytics(models.Model):
    """Analytics for course performance and engagement"""
    
    course = models.OneToOneField('courses.Course', on_delete=models.CASCADE, related_name='analytics')
    
    # Enrollment metrics
    total_enrollments = models.PositiveIntegerField(default=0)
    active_students = models.PositiveIntegerField(default=0)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    dropout_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Performance metrics
    average_grade = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    average_completion_time = models.DurationField(default=timedelta(0))
    exercise_success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Engagement metrics
    average_study_time_per_student = models.DurationField(default=timedelta(0))
    forum_activity_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    collaboration_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Content analytics
    most_difficult_lessons = models.JSONField(default=list)
    most_helpful_lessons = models.JSONField(default=list)
    bottleneck_exercises = models.JSONField(default=list)
    
    # Student feedback
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    satisfaction_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Trends
    enrollment_trend = models.JSONField(default=list)  # Time series data
    completion_trend = models.JSONField(default=list)
    engagement_trend = models.JSONField(default=list)
    
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Course Analytics')
        verbose_name_plural = _('Course Analytics')
    
    def __str__(self):
        return f"Analytics for {self.course.title}"


class InstructorAnalytics(models.Model):
    """Analytics for instructor performance"""
    
    instructor = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_analytics')
    
    # Teaching metrics
    total_courses_taught = models.PositiveIntegerField(default=0)
    total_students_taught = models.PositiveIntegerField(default=0)
    average_course_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    student_satisfaction_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Content creation
    lessons_created = models.PositiveIntegerField(default=0)
    exercises_created = models.PositiveIntegerField(default=0)
    content_quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Student outcomes
    average_student_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    average_student_performance = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    student_success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Engagement
    response_time_to_questions = models.DurationField(default=timedelta(0))
    forum_participation = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    office_hours_utilization = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Professional development
    skills_taught = models.JSONField(default=list)
    certifications = models.JSONField(default=list)
    professional_growth_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Instructor Analytics')
        verbose_name_plural = _('Instructor Analytics')
    
    def __str__(self):
        return f"Instructor analytics for {self.instructor.get_full_name()}"


class PlatformAnalytics(models.Model):
    """Overall platform analytics and metrics"""
    
    date = models.DateField(unique=True)
    
    # User metrics
    total_users = models.PositiveIntegerField(default=0)
    active_users_daily = models.PositiveIntegerField(default=0)
    new_registrations = models.PositiveIntegerField(default=0)
    user_retention_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Course metrics
    total_courses = models.PositiveIntegerField(default=0)
    courses_published = models.PositiveIntegerField(default=0)
    total_enrollments = models.PositiveIntegerField(default=0)
    course_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    # Learning metrics
    total_study_time = models.DurationField(default=timedelta(0))
    exercises_completed = models.PositiveIntegerField(default=0)
    projects_completed = models.PositiveIntegerField(default=0)
    certificates_issued = models.PositiveIntegerField(default=0)
    
    # Engagement metrics
    collaboration_sessions = models.PositiveIntegerField(default=0)
    ai_interactions = models.PositiveIntegerField(default=0)
    help_requests = models.PositiveIntegerField(default=0)
    forum_posts = models.PositiveIntegerField(default=0)
    
    # Quality metrics
    average_course_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    student_satisfaction = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    platform_uptime = models.DecimalField(max_digits=5, decimal_places=2, default=100.0)
    
    # Performance metrics
    average_response_time = models.DecimalField(max_digits=8, decimal_places=3, default=0.0)  # seconds
    code_execution_success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    ai_accuracy_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Platform Analytics')
        verbose_name_plural = _('Platform Analytics')
        ordering = ['-date']
    
    def __str__(self):
        return f"Platform analytics for {self.date}"