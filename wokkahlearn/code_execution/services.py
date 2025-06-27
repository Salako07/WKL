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
    exercise = models.ForeignKey('courses.Exercise', on_delete=models.CASCADE, related_name='test_cases')
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


# code_execution/services.py
import docker
import asyncio
import json
import time
import tempfile
import os
from django.conf import settings
from typing import Dict, Any, Optional
from .models import CodeExecution, ExecutionEnvironment, TestCase, TestResult


class CodeExecutionService:
    """Service for executing code in Docker containers"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.network_name = getattr(settings, 'DOCKER_NETWORK', 'wokkahlearn_execution')
    
    async def execute_code(self, execution: CodeExecution) -> Dict[str, Any]:
        """Execute code and return results"""
        try:
            execution.status = CodeExecution.Status.RUNNING
            execution.started_at = timezone.now()
            execution.save()
            
            # Prepare execution environment
            container_config = self._prepare_container_config(execution)
            
            # Create and start container
            container = self.docker_client.containers.run(
                **container_config,
                detach=True
            )
            
            execution.container_id = container.id
            execution.save()
            
            # Wait for execution to complete
            result = await self._wait_for_completion(container, execution)
            
            # Update execution with results
            execution.stdout_output = result.get('stdout', '')
            execution.stderr_output = result.get('stderr', '')
            execution.exit_code = result.get('exit_code', -1)
            execution.execution_time = result.get('execution_time', 0)
            execution.memory_used = result.get('memory_used', 0)
            execution.status = CodeExecution.Status.COMPLETED
            execution.completed_at = timezone.now()
            execution.save()
            
            # Clean up container
            container.remove()
            
            return result
            
        except docker.errors.ContainerError as e:
            execution.status = CodeExecution.Status.FAILED
            execution.stderr_output = str(e)
            execution.completed_at = timezone.now()
            execution.save()
            raise
        
        except Exception as e:
            execution.status = CodeExecution.Status.FAILED
            execution.stderr_output = f"Internal error: {str(e)}"
            execution.completed_at = timezone.now()
            execution.save()
            raise
    
    def _prepare_container_config(self, execution: CodeExecution) -> Dict[str, Any]:
        """Prepare Docker container configuration"""
        env = execution.environment
        
        # Create temporary file with user code
        code_file = self._create_code_file(execution)
        
        config = {
            'image': env.docker_image,
            'command': self._build_command(execution, code_file),
            'mem_limit': f"{env.max_memory}m",
            'cpu_period': 100000,
            'cpu_quota': env.max_cpu_time * 1000,
            'network': self.network_name,
            'remove': False,
            'detach': True,
            'volumes': {
                os.path.dirname(code_file): {
                    'bind': '/workspace',
                    'mode': 'ro'
                }
            },
            'working_dir': '/workspace',
            'user': 'nobody',
            'read_only': True,
            'tmpfs': {'/tmp': 'noexec,nosuid,size=10m'},
            'security_opt': ['no-new-privileges'],
            'cap_drop': ['ALL'],
            'environment': {
                'TIMEOUT': str(env.default_timeout),
                'MAX_MEMORY': str(env.max_memory),
            }
        }
        
        # Add stdin if provided
        if execution.stdin_input:
            config['stdin_open'] = True
            config['tty'] = False
        
        return config
    
    def _create_code_file(self, execution: CodeExecution) -> str:
        """Create temporary file with user code"""
        env = execution.environment
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix='wokkah_exec_')
        
        # Write code to file
        filename = f"user_code{env.file_extension}"
        filepath = os.path.join(temp_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(execution.source_code)
        
        return filepath
    
    def _build_command(self, execution: CodeExecution, code_file: str) -> list:
        """Build execution command"""
        env = execution.environment
        filename = os.path.basename(code_file)
        
        if env.interpreter_command:
            cmd = [env.interpreter_command, filename]
        elif env.compiler_command:
            # For compiled languages, compile first then run
            output_file = filename.replace(env.file_extension, '')
            cmd = [
                'sh', '-c',
                f"{env.compiler_command} {filename} -o {output_file} && ./{output_file}"
            ]
        else:
            # Default command
            cmd = [filename]
        
        # Add command line arguments
        if execution.command_line_args:
            cmd.extend(execution.command_line_args)
        
        return cmd
    
    async def _wait_for_completion(self, container, execution: CodeExecution) -> Dict[str, Any]:
        """Wait for container execution to complete"""
        start_time = time.time()
        timeout = execution.environment.default_timeout
        
        try:
            # Wait for container to complete or timeout
            result = container.wait(timeout=timeout)
            execution_time = time.time() - start_time
            
            # Get output
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8')
            
            # Get resource usage
            stats = container.stats(stream=False)
            memory_used = stats['memory_stats'].get('max_usage', 0) // (1024 * 1024)  # Convert to MB
            
            return {
                'exit_code': result['StatusCode'],
                'stdout': stdout,
                'stderr': stderr,
                'execution_time': execution_time,
                'memory_used': memory_used
            }
            
        except docker.errors.APIError as e:
            if 'timeout' in str(e).lower():
                execution.status = CodeExecution.Status.TIMEOUT
                execution.save()
                container.stop()
                return {
                    'exit_code': -1,
                    'stdout': '',
                    'stderr': 'Execution timed out',
                    'execution_time': timeout,
                    'memory_used': 0
                }
            raise
    
    async def run_test_cases(self, execution: CodeExecution) -> list:
        """Run test cases for an exercise submission"""
        if not execution.exercise:
            return []
        
        test_cases = execution.exercise.test_cases.filter(is_required=True)
        results = []
        
        for test_case in test_cases:
            result = await self._run_single_test(execution, test_case)
            results.append(result)
        
        return results
    
    async def _run_single_test(self, execution: CodeExecution, test_case: TestCase) -> TestResult:
        """Run a single test case"""
        # Create test execution
        test_execution = CodeExecution.objects.create(
            user=execution.user,
            environment=execution.environment,
            execution_type=CodeExecution.ExecutionType.TEST,
            source_code=self._build_test_code(execution.source_code, test_case),
            stdin_input=test_case.input_data
        )
        
        # Execute test
        try:
            result = await self.execute_code(test_execution)
            
            # Create test result
            test_result = TestResult.objects.create(
                execution=execution,
                test_case=test_case,
                status=self._determine_test_status(result, test_case),
                actual_output=result.get('stdout', ''),
                error_message=result.get('stderr', ''),
                execution_time=result.get('execution_time', 0),
                memory_used=result.get('memory_used', 0),
                points_earned=test_case.points if result.get('exit_code') == 0 else 0,
                points_possible=test_case.points
            )
            
            return test_result
            
        except Exception as e:
            # Create failed test result
            test_result = TestResult.objects.create(
                execution=execution,
                test_case=test_case,
                status=TestResult.Status.ERROR,
                error_message=str(e),
                points_earned=0,
                points_possible=test_case.points
            )
            
            return test_result
    
    def _build_test_code(self, user_code: str, test_case: TestCase) -> str:
        """Build code with test case"""
        test_code = ""
        
        if test_case.setup_code:
            test_code += test_case.setup_code + "\n\n"
        
        test_code += user_code + "\n\n"
        
        if test_case.test_code:
            test_code += test_case.test_code + "\n\n"
        
        if test_case.teardown_code:
            test_code += test_case.teardown_code + "\n"
        
        return test_code
    
    def _determine_test_status(self, execution_result: Dict[str, Any], test_case: TestCase) -> str:
        """Determine test result status"""
        if execution_result.get('exit_code') != 0:
            return TestResult.Status.ERROR
        
        actual_output = execution_result.get('stdout', '').strip()
        expected_output = test_case.expected_output.strip()
        
        if actual_output == expected_output:
            return TestResult.Status.PASSED
        else:
            return TestResult.Status.FAILED