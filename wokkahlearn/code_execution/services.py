# code_execution/services.py
import docker
import asyncio
import json
import time
import tempfile
import os
from datetime import timezone
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