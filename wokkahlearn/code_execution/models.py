# code_execution/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json

User = get_user_model()


class ExecutionEnvironment(models.Model):
    """Execution environments for different programming languages"""
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        MAINTENANCE = 'maintenance', _('Maintenance')
        DEPRECATED = 'deprecated', _('Deprecated')
        DISABLED = 'disabled', _('Disabled')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    language = models.CharField(max_length=50)
    version = models.CharField(max_length=20)
    docker_image = models.CharField(max_length=200)
    
    # Environment configuration
    default_timeout = models.PositiveIntegerField(default=30)  # seconds
    max_memory = models.PositiveIntegerField(default=128)  # MB
    max_cpu_time = models.PositiveIntegerField(default=10)  # seconds
    max_file_size = models.PositiveIntegerField(default=10)  # MB
    
    # Supported features
    supports_input = models.BooleanField(default=True)
    supports_graphics = models.BooleanField(default=False)
    supports_networking = models.BooleanField(default=False)
    supports_file_operations = models.BooleanField(default=True)
    
    # Language-specific settings
    compiler_command = models.CharField(max_length=200, blank=True)
    interpreter_command = models.CharField(max_length=200, blank=True)
    file_extension = models.CharField(max_length=10)
    
    # Pre-installed packages
    installed_packages = models.JSONField(default=list)
    available_libraries = models.JSONField(default=list)
    
    # Security settings
    allowed_imports = models.JSONField(default=list)
    blocked_imports = models.JSONField(default=list)
    blocked_functions = models.JSONField(default=list)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Execution Environment')
        verbose_name_plural = _('Execution Environments')
        unique_together = ['language', 'version']
        ordering = ['language', 'version']
    
    def __str__(self):
        return f"{self.language} {self.version}"


class CodeExecution(models.Model):
    """Track code execution requests and results"""
    
    class ExecutionType(models.TextChoices):
        EXERCISE = 'exercise', _('Exercise Submission')
        PLAYGROUND = 'playground', _('Playground Code')
        TEST = 'test', _('Test Run')
        DEBUG = 'debug', _('Debug Session')
        DEMO = 'demo', _('Demo Code')
    
    class Status(models.TextChoices):
        QUEUED = 'queued', _('Queued')
        RUNNING = 'running', _('Running')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
        TIMEOUT = 'timeout', _('Timeout')
        MEMORY_LIMIT = 'memory_limit', _('Memory Limit Exceeded')
        SECURITY_VIOLATION = 'security_violation', _('Security Violation')
        CANCELLED = 'cancelled', _('Cancelled')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='code_executions')
    environment = models.ForeignKey(ExecutionEnvironment, on_delete=models.CASCADE)
    execution_type = models.CharField(max_length=20, choices=ExecutionType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    
    # Code and input
    source_code = models.TextField()
    stdin_input = models.TextField(blank=True)
    command_line_args = models.JSONField(default=list)
    
    # Execution results
    stdout_output = models.TextField(blank=True)
    stderr_output = models.TextField(blank=True)
    exit_code = models.IntegerField(null=True, blank=True)
    
    # Resource usage
    execution_time = models.FloatField(null=True, blank=True)  # seconds
    memory_used = models.PositiveIntegerField(null=True, blank=True)  # MB
    cpu_time = models.FloatField(null=True, blank=True)  # seconds
    
    # System information
    container_id = models.CharField(max_length=100, blank=True)
    worker_node = models.CharField(max_length=100, blank=True)
    
    # Context information
    exercise = models.ForeignKey('courses.Exercise', on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    # Security and compliance
    security_violations = models.JSONField(default=list)
    blocked_operations = models.JSONField(default=list)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Code Execution')
        verbose_name_plural = _('Code Executions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['environment', 'status']),
            models.Index(fields=['exercise', 'user']),
        ]
    
    def __str__(self):
        return f"Execution {self.id} - {self.user.username} ({self.environment.language})"
    
    @property
    def is_successful(self):
        return self.status == self.Status.COMPLETED and self.exit_code == 0


class TestCase(models.Model):
    """Test cases for exercise validation"""
    
    class TestType(models.TextChoices):
        UNIT = 'unit', _('Unit Test')
        INTEGRATION = 'integration', _('Integration Test')
        INPUT_OUTPUT = 'input_output', _('Input/Output Test')
        PERFORMANCE = 'performance', _('Performance Test')
        MEMORY = 'memory', _('Memory Test')
        CUSTOM = 'custom', _('Custom Test')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exercise = models.ForeignKey('courses.Exercise', on_delete=models.CASCADE, related_name='test_case_object')
    name = models.CharField(max_length=200)
    test_type = models.CharField(max_length=20, choices=TestType.choices)
    description = models.TextField(blank=True)
    
    # Test data
    input_data = models.TextField(blank=True)
    expected_output = models.TextField(blank=True)
    expected_error = models.TextField(blank=True)
    
    # Test code
    setup_code = models.TextField(blank=True)
    test_code = models.TextField(blank=True)
    teardown_code = models.TextField(blank=True)
    
    # Test configuration
    timeout = models.PositiveIntegerField(default=10)  # seconds
    max_memory = models.PositiveIntegerField(default=64)  # MB
    points = models.PositiveIntegerField(default=1)
    is_hidden = models.BooleanField(default=False)
    is_required = models.BooleanField(default=True)
    
    # Test metadata
    order = models.PositiveIntegerField(default=0)
    weight = models.FloatField(default=1.0)
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard')
        ],
        default='medium'
    )
    
    # Performance requirements
    max_execution_time = models.FloatField(null=True, blank=True)
    max_memory_usage = models.PositiveIntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Test Case')
        verbose_name_plural = _('Test Cases')
        ordering = ['exercise', 'order']
    
    def __str__(self):
        return f"{self.exercise.title} - {self.name}"


class TestResult(models.Model):
    """Results of running test cases"""
    
    class Status(models.TextChoices):
        PASSED = 'passed', _('Passed')
        FAILED = 'failed', _('Failed')
        ERROR = 'error', _('Error')
        TIMEOUT = 'timeout', _('Timeout')
        MEMORY_EXCEEDED = 'memory_exceeded', _('Memory Exceeded')
        SKIPPED = 'skipped', _('Skipped')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(CodeExecution, on_delete=models.CASCADE, related_name='test_results')
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices)
    
    # Test output
    actual_output = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    stack_trace = models.TextField(blank=True)
    
    # Performance metrics
    execution_time = models.FloatField(null=True, blank=True)
    memory_used = models.PositiveIntegerField(null=True, blank=True)
    
    # Scoring
    points_earned = models.PositiveIntegerField(default=0)
    points_possible = models.PositiveIntegerField(default=0)
    
    # Comparison details
    output_diff = models.TextField(blank=True)
    similarity_score = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Test Result')
        verbose_name_plural = _('Test Results')
        unique_together = ['execution', 'test_case']
    
    def __str__(self):
        return f"{self.test_case.name} - {self.get_status_display()}"
    
    @property
    def is_passed(self):
        return self.status == self.Status.PASSED


class CodePlayground(models.Model):
    """Code playground sessions for experimentation"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playground_sessions')
    title = models.CharField(max_length=200, blank=True)
    environment = models.ForeignKey(ExecutionEnvironment, on_delete=models.CASCADE)
    
    # Code content
    source_code = models.TextField(default='')
    
    # Session metadata
    is_public = models.BooleanField(default=False)
    is_shared = models.BooleanField(default=False)
    shared_url = models.CharField(max_length=100, blank=True, unique=True)
    
    # Collaboration
    collaborators = models.ManyToManyField(User, blank=True, related_name='shared_playgrounds')
    allow_editing = models.BooleanField(default=False)
    
    # Usage tracking
    execution_count = models.PositiveIntegerField(default=0)
    last_executed = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Code Playground')
        verbose_name_plural = _('Code Playgrounds')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username}'s {self.environment.language} playground"


class CodeTemplate(models.Model):
    """Code templates for different exercises and languages"""
    
    class TemplateType(models.TextChoices):
        STARTER = 'starter', _('Starter Template')
        SOLUTION = 'solution', _('Solution Template')
        EXAMPLE = 'example', _('Example Code')
        BOILERPLATE = 'boilerplate', _('Boilerplate')
        FRAMEWORK = 'framework', _('Framework Template')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=20, choices=TemplateType.choices)
    environment = models.ForeignKey(ExecutionEnvironment, on_delete=models.CASCADE)
    
    # Template content
    code_template = models.TextField()
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    
    # Template metadata
    tags = models.JSONField(default=list)
    difficulty_level = models.CharField(max_length=20, default='beginner')
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Author information
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='code_templates')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Code Template')
        verbose_name_plural = _('Code Templates')
        ordering = ['environment', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.environment.language})"


class ExecutionQuota(models.Model):
    """Track user execution quotas and limits"""
    
    class QuotaType(models.TextChoices):
        DAILY = 'daily', _('Daily Quota')
        MONTHLY = 'monthly', _('Monthly Quota')
        TOTAL = 'total', _('Total Quota')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='execution_quotas')
    quota_type = models.CharField(max_length=10, choices=QuotaType.choices)
    
    # Quota limits
    max_executions = models.PositiveIntegerField()
    max_execution_time = models.PositiveIntegerField()  # total seconds allowed
    max_memory_usage = models.PositiveIntegerField()  # total MB allowed
    
    # Current usage
    executions_used = models.PositiveIntegerField(default=0)
    execution_time_used = models.PositiveIntegerField(default=0)
    memory_usage_used = models.PositiveIntegerField(default=0)
    
    # Reset tracking
    last_reset = models.DateTimeField(auto_now_add=True)
    next_reset = models.DateTimeField()
    
    # Status
    is_active = models.BooleanField(default=True)
    is_exceeded = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Execution Quota')
        verbose_name_plural = _('Execution Quotas')
        unique_together = ['user', 'quota_type']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_quota_type_display()}"
    
    def check_quota(self):
        """Check if user has exceeded quota"""
        if (self.executions_used >= self.max_executions or
            self.execution_time_used >= self.max_execution_time or
            self.memory_usage_used >= self.max_memory_usage):
            self.is_exceeded = True
            self.save()
            return False
        return True
    
    def reset_quota(self):
        """Reset quota counters"""
        self.executions_used = 0
        self.execution_time_used = 0
        self.memory_usage_used = 0
        self.is_exceeded = False
        from django.utils import timezone
        self.last_reset = timezone.now()
        
        # Calculate next reset time based on quota type
        if self.quota_type == self.QuotaType.DAILY:
            from datetime import timedelta
            self.next_reset = self.last_reset + timedelta(days=1)
        elif self.quota_type == self.QuotaType.MONTHLY:
            from datetime import timedelta
            self.next_reset = self.last_reset + timedelta(days=30)
        
        self.save()