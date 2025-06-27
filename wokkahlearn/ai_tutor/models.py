# ai_tutor/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json

User = get_user_model()


class AIModel(models.Model):
    """AI models available for different tasks"""
    
    class ModelType(models.TextChoices):
        CODE_ASSISTANT = 'code_assistant', _('Code Assistant')
        TUTOR = 'tutor', _('AI Tutor')
        REVIEWER = 'reviewer', _('Code Reviewer')
        EXPLAINER = 'explainer', _('Concept Explainer')
        QUIZ_GENERATOR = 'quiz_generator', _('Quiz Generator')
        CURRICULUM = 'curriculum', _('Curriculum Planner')
    
    class Provider(models.TextChoices):
        OPENAI = 'openai', _('OpenAI')
        ANTHROPIC = 'anthropic', _('Anthropic')
        COHERE = 'cohere', _('Cohere')
        HUGGINGFACE = 'huggingface', _('Hugging Face')
        LOCAL = 'local', _('Local Model')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=20, choices=ModelType.choices)
    provider = models.CharField(max_length=20, choices=Provider.choices)
    model_id = models.CharField(max_length=200, help_text="Provider-specific model identifier")
    
    # Model configuration
    max_tokens = models.PositiveIntegerField(default=4096)
    temperature = models.FloatField(default=0.7, validators=[MinValueValidator(0), MaxValueValidator(2)])
    top_p = models.FloatField(default=1.0, validators=[MinValueValidator(0), MaxValueValidator(1)])
    
    # Model capabilities
    supports_code = models.BooleanField(default=True)
    supports_streaming = models.BooleanField(default=False)
    supports_function_calling = models.BooleanField(default=False)
    programming_languages = models.JSONField(default=list)
    
    # Performance and limits
    cost_per_token = models.DecimalField(max_digits=10, decimal_places=8, default=0.0)
    rate_limit_per_minute = models.PositiveIntegerField(default=60)
    average_response_time = models.FloatField(default=0.0)  # seconds
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('AI Model')
        verbose_name_plural = _('AI Models')
        ordering = ['model_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_model_type_display()})"


class AITutorSession(models.Model):
    """AI tutoring sessions with students"""
    
    class SessionType(models.TextChoices):
        HELP_REQUEST = 'help_request', _('Help Request')
        CODE_REVIEW = 'code_review', _('Code Review')
        CONCEPT_EXPLANATION = 'concept_explanation', _('Concept Explanation')
        DEBUGGING = 'debugging', _('Debugging Assistance')
        LEARNING_PATH = 'learning_path', _('Learning Path Guidance')
        ASSESSMENT = 'assessment', _('Assessment and Feedback')
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        COMPLETED = 'completed', _('Completed')
        PAUSED = 'paused', _('Paused')
        TERMINATED = 'terminated', _('Terminated')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_sessions')
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE)
    session_type = models.CharField(max_length=20, choices=SessionType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    
    # Session context
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, null=True, blank=True)
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, null=True, blank=True)
    exercise = models.ForeignKey('courses.Exercise', on_delete=models.CASCADE, null=True, blank=True)
    
    # Session metadata
    title = models.CharField(max_length=200, blank=True)
    initial_query = models.TextField()
    context_data = models.JSONField(default=dict)  # Student code, difficulty level, etc.
    
    # Session tracking
    total_messages = models.PositiveIntegerField(default=0)
    total_tokens_used = models.PositiveIntegerField(default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0.0)
    
    # Quality metrics
    student_satisfaction = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    helpfulness_rating = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('AI Tutor Session')
        verbose_name_plural = _('AI Tutor Sessions')
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['session_type', 'started_at']),
        ]
    
    def __str__(self):
        return f"AI Session: {self.student.get_full_name()} - {self.get_session_type_display()}"


class AIMessage(models.Model):
    """Individual messages in AI tutor sessions"""
    
    class MessageType(models.TextChoices):
        USER = 'user', _('User Message')
        ASSISTANT = 'assistant', _('AI Assistant')
        SYSTEM = 'system', _('System Message')
        TOOL = 'tool', _('Tool Response')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(AITutorSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=20, choices=MessageType.choices)
    content = models.TextField()
    
    # Message metadata
    tokens_used = models.PositiveIntegerField(default=0)
    response_time = models.FloatField(default=0.0)  # seconds
    
    # Code analysis (if applicable)
    code_language = models.CharField(max_length=50, blank=True)
    code_analysis = models.JSONField(default=dict)
    suggested_improvements = models.JSONField(default=list)
    
    # Learning context
    concepts_referenced = models.JSONField(default=list)
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('basic', 'Basic'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ],
        blank=True
    )
    
    # Interaction metadata
    requires_human_review = models.BooleanField(default=False)
    confidence_score = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('AI Message')
        verbose_name_plural = _('AI Messages')
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.get_message_type_display()} - {self.content[:50]}"


class LearningPathRecommendation(models.Model):
    """AI-generated learning path recommendations"""
    
    class RecommendationType(models.TextChoices):
        NEXT_COURSE = 'next_course', _('Next Course')
        SKILL_GAP = 'skill_gap', _('Skill Gap Analysis')
        REVIEW_TOPIC = 'review_topic', _('Review Topic')
        ADVANCED_TOPIC = 'advanced_topic', _('Advanced Topic')
        PROJECT_IDEA = 'project_idea', _('Project Idea')
        PRACTICE_EXERCISE = 'practice_exercise', _('Practice Exercise')
    
    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        URGENT = 'urgent', _('Urgent')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_recommendations')
    recommendation_type = models.CharField(max_length=20, choices=RecommendationType.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    
    # Recommendation content
    title = models.CharField(max_length=200)
    description = models.TextField()
    reasoning = models.TextField(help_text="AI reasoning for this recommendation")
    
    # Linked resources
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, null=True, blank=True)
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, null=True, blank=True)
    exercise = models.ForeignKey('courses.Exercise', on_delete=models.CASCADE, null=True, blank=True)
    external_resource = models.URLField(blank=True)
    
    # Recommendation metadata
    confidence_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    estimated_completion_time = models.DurationField()
    skill_level_required = models.CharField(max_length=20, default='beginner')
    
    # Tracking
    is_accepted = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # AI model used
    generated_by = models.ForeignKey(AIModel, on_delete=models.CASCADE)
    generation_context = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Learning Path Recommendation')
        verbose_name_plural = _('Learning Path Recommendations')
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['student', 'is_dismissed']),
            models.Index(fields=['recommendation_type', 'priority']),
        ]
    
    def __str__(self):
        return f"Recommendation for {self.student.get_full_name()}: {self.title}"


class CodeAnalysisResult(models.Model):
    """AI analysis results for student code"""
    
    class AnalysisType(models.TextChoices):
        SYNTAX_CHECK = 'syntax_check', _('Syntax Check')
        STYLE_REVIEW = 'style_review', _('Style Review')
        PERFORMANCE = 'performance', _('Performance Analysis')
        SECURITY = 'security', _('Security Analysis')
        BEST_PRACTICES = 'best_practices', _('Best Practices')
        DEBUGGING = 'debugging', _('Debugging Help')
        OPTIMIZATION = 'optimization', _('Optimization Suggestions')
    
    class Severity(models.TextChoices):
        INFO = 'info', _('Information')
        WARNING = 'warning', _('Warning')
        ERROR = 'error', _('Error')
        CRITICAL = 'critical', _('Critical')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey('courses.ExerciseSubmission', on_delete=models.CASCADE, related_name='ai_analysis')
    analysis_type = models.CharField(max_length=20, choices=AnalysisType.choices)
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE)
    
    # Analysis results
    overall_score = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    issues_found = models.JSONField(default=list)
    suggestions = models.JSONField(default=list)
    strengths = models.JSONField(default=list)
    
    # Detailed feedback
    summary = models.TextField()
    detailed_feedback = models.TextField()
    improvement_suggestions = models.TextField()
    
    # Code quality metrics
    complexity_score = models.PositiveIntegerField(null=True, blank=True)
    readability_score = models.PositiveIntegerField(null=True, blank=True)
    maintainability_score = models.PositiveIntegerField(null=True, blank=True)
    
    # Learning insights
    concepts_demonstrated = models.JSONField(default=list)
    missing_concepts = models.JSONField(default=list)
    next_learning_steps = models.JSONField(default=list)
    
    # Analysis metadata
    analysis_duration = models.FloatField(default=0.0)  # seconds
    tokens_used = models.PositiveIntegerField(default=0)
    confidence_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Code Analysis Result')
        verbose_name_plural = _('Code Analysis Results')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Analysis: {self.submission.exercise.title} - {self.get_analysis_type_display()}"


class PersonalizedQuiz(models.Model):
    """AI-generated personalized quizzes"""
    
    class QuizType(models.TextChoices):
        KNOWLEDGE_CHECK = 'knowledge_check', _('Knowledge Check')
        SKILL_ASSESSMENT = 'skill_assessment', _('Skill Assessment')
        REVIEW_QUIZ = 'review_quiz', _('Review Quiz')
        CHALLENGE = 'challenge', _('Challenge Quiz')
        DIAGNOSTIC = 'diagnostic', _('Diagnostic Quiz')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personalized_quizzes')
    quiz_type = models.CharField(max_length=20, choices=QuizType.choices)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Quiz content
    questions = models.JSONField(default=list)
    correct_answers = models.JSONField(default=list)
    explanations = models.JSONField(default=list)
    
    # Quiz settings
    difficulty_level = models.CharField(max_length=20, default='intermediate')
    estimated_duration = models.DurationField()
    topics_covered = models.JSONField(default=list)
    
    # Personalization
    based_on_weaknesses = models.JSONField(default=list)
    adaptation_reason = models.TextField()
    
    # AI generation
    generated_by = models.ForeignKey(AIModel, on_delete=models.CASCADE)
    generation_prompt = models.TextField()
    generation_context = models.JSONField(default=dict)
    
    # Usage tracking
    times_taken = models.PositiveIntegerField(default=0)
    average_score = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Personalized Quiz')
        verbose_name_plural = _('Personalized Quizzes')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Quiz for {self.student.get_full_name()}: {self.title}"


class AITutorFeedback(models.Model):
    """Feedback and ratings for AI tutor interactions"""
    
    session = models.OneToOneField(AITutorSession, on_delete=models.CASCADE, related_name='feedback')
    
    # Quantitative feedback
    overall_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    helpfulness = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    accuracy = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    clarity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    response_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Qualitative feedback
    what_worked_well = models.TextField(blank=True)
    what_could_improve = models.TextField(blank=True)
    additional_comments = models.TextField(blank=True)
    
    # Problem resolution
    problem_solved = models.BooleanField()
    would_recommend = models.BooleanField()
    
    # Follow-up
    needs_human_tutor = models.BooleanField(default=False)
    suggested_improvements = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('AI Tutor Feedback')
        verbose_name_plural = _('AI Tutor Feedback')
    
    def __str__(self):
        return f"Feedback for session {self.session.id} - {self.overall_rating}/5"


class AIModelUsageStats(models.Model):
    """Track AI model usage statistics"""
    
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name='usage_stats')
    date = models.DateField()
    
    # Usage metrics
    total_requests = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0.0)
    
    # Performance metrics
    average_response_time = models.FloatField(default=0.0)
    success_rate = models.FloatField(default=100.0)
    error_count = models.PositiveIntegerField(default=0)
    
    # User satisfaction
    average_rating = models.FloatField(default=0.0)
    total_feedback_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('AI Model Usage Stats')
        verbose_name_plural = _('AI Model Usage Stats')
        unique_together = ['ai_model', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.ai_model.name} - {self.date}"