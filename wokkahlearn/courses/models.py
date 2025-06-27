# courses/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
import uuid
from datetime import timedelta

User = get_user_model()


class CourseCategory(models.Model):
    """Categories for organizing courses"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=7, default='#000000')  # Hex color
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Course Category')
        verbose_name_plural = _('Course Categories')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Course(models.Model):
    """Main course model"""
    
    class DifficultyLevel(models.TextChoices):
        BEGINNER = 'beginner', _('Beginner')
        INTERMEDIATE = 'intermediate', _('Intermediate')
        ADVANCED = 'advanced', _('Advanced')
        EXPERT = 'expert', _('Expert')
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        REVIEW = 'review', _('Under Review')
        PUBLISHED = 'published', _('Published')
        ARCHIVED = 'archived', _('Archived')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300)
    
    # Content organization
    category = models.ForeignKey(CourseCategory, on_delete=models.SET_NULL, null=True)
    tags = models.JSONField(default=list, help_text="List of tags for the course")
    
    # Course metadata
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='taught_courses')
    co_instructors = models.ManyToManyField(User, blank=True, related_name='co_taught_courses')
    difficulty_level = models.CharField(max_length=20, choices=DifficultyLevel.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    
    # Course media
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)
    preview_video = models.URLField(blank=True, help_text="Preview video URL")
    
    # Course structure
    estimated_duration = models.DurationField(help_text="Estimated completion time")
    total_lessons = models.PositiveIntegerField(default=0)
    total_exercises = models.PositiveIntegerField(default=0)
    
    # Prerequisites and requirements
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False)
    required_skills = models.JSONField(default=list, help_text="Required skills to start")
    programming_languages = models.JSONField(default=list, help_text="Programming languages used")
    
    # Pricing and access
    is_free = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    premium_only = models.BooleanField(default=False)
    
    # Learning objectives
    learning_objectives = models.JSONField(default=list, help_text="What students will learn")
    skills_gained = models.JSONField(default=list, help_text="Skills students will gain")
    
    # Settings
    allow_enrollment = models.BooleanField(default=True)
    max_students = models.PositiveIntegerField(null=True, blank=True)
    certificate_enabled = models.BooleanField(default=True)
    discussion_enabled = models.BooleanField(default=True)
    
    # Analytics
    total_enrollments = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_reviews = models.PositiveIntegerField(default=0)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'difficulty_level']),
            models.Index(fields=['category', 'is_free']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED
    
    def can_enroll(self, user):
        """Check if user can enroll in this course"""
        if not self.allow_enrollment or not self.is_published:
            return False
        
        if self.premium_only and not user.is_premium:
            return False
        
        if self.max_students:
            if self.total_enrollments >= self.max_students:
                return False
        
        return True


class Module(models.Model):
    """Course modules for organizing lessons"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    # Module settings
    is_required = models.BooleanField(default=True)
    estimated_duration = models.DurationField()
    
    # Prerequisites
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Module')
        verbose_name_plural = _('Modules')
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    """Individual lessons within modules"""
    
    class LessonType(models.TextChoices):
        VIDEO = 'video', _('Video Lesson')
        TEXT = 'text', _('Text/Reading')
        INTERACTIVE = 'interactive', _('Interactive Content')
        QUIZ = 'quiz', _('Quiz')
        EXERCISE = 'exercise', _('Coding Exercise')
        PROJECT = 'project', _('Project')
        LIVE = 'live', _('Live Session')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    lesson_type = models.CharField(max_length=20, choices=LessonType.choices)
    description = models.TextField(blank=True)
    
    # Content
    content = models.TextField(blank=True, help_text="Main lesson content (markdown)")
    video_url = models.URLField(blank=True)
    video_duration = models.DurationField(null=True, blank=True)
    
    # Lesson structure
    order = models.PositiveIntegerField(default=0)
    estimated_duration = models.DurationField()
    
    # Settings
    is_preview = models.BooleanField(default=False, help_text="Available without enrollment")
    is_required = models.BooleanField(default=True)
    allow_discussion = models.BooleanField(default=True)
    
    # Prerequisites
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    # Resources
    additional_resources = models.JSONField(
        default=list,
        help_text="Additional resources like links, files, etc."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Lesson')
        verbose_name_plural = _('Lessons')
        ordering = ['module', 'order']
        unique_together = ['module', 'order']
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Exercise(models.Model):
    """Coding exercises for lessons"""
    
    class ExerciseType(models.TextChoices):
        CODING = 'coding', _('Coding Exercise')
        QUIZ = 'quiz', _('Quiz')
        FILL_BLANK = 'fill_blank', _('Fill in the Blanks')
        MULTIPLE_CHOICE = 'multiple_choice', _('Multiple Choice')
        DRAG_DROP = 'drag_drop', _('Drag and Drop')
        PROJECT = 'project', _('Project Assignment')
    
    class Difficulty(models.TextChoices):
        EASY = 'easy', _('Easy')
        MEDIUM = 'medium', _('Medium')
        HARD = 'hard', _('Hard')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='exercises')
    title = models.CharField(max_length=200)
    exercise_type = models.CharField(max_length=20, choices=ExerciseType.choices)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.EASY)
    
    # Exercise content
    description = models.TextField(help_text="Exercise description and instructions")
    starter_code = models.TextField(blank=True, help_text="Starter code for students")
    solution_code = models.TextField(blank=True, help_text="Reference solution")
    
    # Programming language and environment
    programming_language = models.CharField(max_length=50, default='python')
    environment_config = models.JSONField(
        default=dict,
        help_text="Environment configuration for code execution"
    )
    
    # Testing and validation
    test_cases = models.JSONField(
        default=list,
        help_text="Test cases for automatic grading"
    )
    validation_code = models.TextField(
        blank=True,
        help_text="Custom validation code"
    )
    
    # Exercise settings
    order = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(null=True, blank=True)
    time_limit = models.DurationField(null=True, blank=True)
    points = models.PositiveIntegerField(default=10)
    
    # AI assistance
    ai_hints_enabled = models.BooleanField(default=True)
    ai_explanation_enabled = models.BooleanField(default=True)
    hint_penalty = models.PositiveIntegerField(default=0, help_text="Points deducted for hints")
    
    # Collaboration
    allow_collaboration = models.BooleanField(default=False)
    peer_review_enabled = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Exercise')
        verbose_name_plural = _('Exercises')
        ordering = ['lesson', 'order']
    
    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class CourseEnrollment(models.Model):
    """Track student enrollments in courses"""
    
    class Status(models.TextChoices):
        ENROLLED = 'enrolled', _('Enrolled')
        COMPLETED = 'completed', _('Completed')
        DROPPED = 'dropped', _('Dropped')
        SUSPENDED = 'suspended', _('Suspended')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ENROLLED)
    
    # Progress tracking
    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    lessons_completed = models.PositiveIntegerField(default=0)
    exercises_completed = models.PositiveIntegerField(default=0)
    
    # Time tracking
    total_study_time = models.DurationField(default=timedelta(0))
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    # Completion
    completed_at = models.DateTimeField(null=True, blank=True)
    certificate_issued = models.BooleanField(default=False)
    certificate_url = models.URLField(blank=True)
    
    # Enrollment details
    enrolled_at = models.DateTimeField(auto_now_add=True)
    enrollment_source = models.CharField(
        max_length=50,
        choices=[
            ('direct', 'Direct Enrollment'),
            ('invitation', 'Invitation'),
            ('organization', 'Organization'),
            ('recommendation', 'AI Recommendation')
        ],
        default='direct'
    )
    
    class Meta:
        verbose_name = _('Course Enrollment')
        verbose_name_plural = _('Course Enrollments')
        unique_together = ['student', 'course']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['course', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.title}"
    
    def update_progress(self):
        """Update enrollment progress based on completed lessons"""
        total_lessons = self.course.total_lessons
        if total_lessons > 0:
            self.progress_percentage = (self.lessons_completed / total_lessons) * 100
            
            if self.progress_percentage >= 100 and self.status == self.Status.ENROLLED:
                self.status = self.Status.COMPLETED
                from django.utils import timezone
                self.completed_at = timezone.now()
        
        self.save()


class LessonProgress(models.Model):
    """Track student progress through individual lessons"""
    
    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', _('Not Started')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)
    
    # Progress details
    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Time tracking
    time_spent = models.DurationField(default=timedelta(0))
    first_accessed = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Interaction data
    notes = models.TextField(blank=True)
    bookmarked = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('Lesson Progress')
        verbose_name_plural = _('Lesson Progress')
        unique_together = ['enrollment', 'lesson']
    
    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} - {self.lesson.title}"


class ExerciseSubmission(models.Model):
    """Track student submissions for exercises"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PASSED = 'passed', _('Passed')
        FAILED = 'failed', _('Failed')
        PARTIAL = 'partial', _('Partial Credit')
        REVIEWING = 'reviewing', _('Under Review')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_submissions')
    
    # Submission data
    submitted_code = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Execution results
    execution_output = models.TextField(blank=True)
    test_results = models.JSONField(default=dict)
    execution_time = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    memory_usage = models.PositiveIntegerField(null=True, blank=True)  # in MB
    
    # Feedback and grading
    ai_feedback = models.TextField(blank=True)
    instructor_feedback = models.TextField(blank=True)
    auto_graded = models.BooleanField(default=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_submissions')
    
    # Submission metadata
    attempt_number = models.PositiveIntegerField(default=1)
    hints_used = models.PositiveIntegerField(default=0)
    time_taken = models.DurationField()
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Exercise Submission')
        verbose_name_plural = _('Exercise Submissions')
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['student', 'exercise']),
            models.Index(fields=['exercise', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.exercise.title} (Attempt {self.attempt_number})"