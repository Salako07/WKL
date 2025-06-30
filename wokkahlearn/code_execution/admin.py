from django.contrib import admin
from .models import (
    ExecutionEnvironment, CodeExecution, TestCase, TestResult, 
    CodePlayground, CodeTemplate, ExecutionQuota
)

@admin.register(ExecutionEnvironment)
class ExecutionEnvironmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'language', 'version', 'status', 'is_default', 'docker_image')
    list_filter = ('language', 'status', 'is_default', 'supports_input', 'supports_graphics')
    search_fields = ('name', 'language', 'version')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'language', 'version', 'docker_image', 'file_extension')
        }),
        ('Resource Limits', {
            'fields': ('default_timeout', 'max_memory', 'max_cpu_time', 'max_file_size')
        }),
        ('Features', {
            'fields': ('supports_input', 'supports_graphics', 'supports_networking', 'supports_file_operations')
        }),
        ('Commands', {
            'fields': ('compiler_command', 'interpreter_command')
        }),
        ('Packages', {
            'fields': ('installed_packages', 'available_libraries')
        }),
        ('Security', {
            'fields': ('allowed_imports', 'blocked_imports', 'blocked_functions')
        }),
        ('Status', {
            'fields': ('status', 'is_default')
        }),
    )

@admin.register(CodeExecution)
class CodeExecutionAdmin(admin.ModelAdmin):
    list_display = ('user', 'environment', 'execution_type', 'status', 'execution_time', 'created_at')
    list_filter = ('execution_type', 'status', 'environment__language')
    search_fields = ('user__username', 'source_code')
    date_hierarchy = 'created_at'
    readonly_fields = ('container_id', 'execution_time', 'memory_used', 'created_at', 'started_at', 'completed_at')

@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ('exercise', 'name', 'test_type', 'difficulty', 'points', 'is_hidden', 'is_required')
    list_filter = ('test_type', 'difficulty', 'is_hidden', 'is_required')
    search_fields = ('exercise__title', 'name', 'description')



