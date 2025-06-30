# accounts/management/commands/setup_initial_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Organization, UserProfile
from courses.models import CourseCategory
from code_execution.models import ExecutionEnvironment
from ai_tutor.models import AIModel
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Set up initial data for WokkahLearn platform'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...')
        
        # Create superuser if doesn't exist
        if not User.objects.filter(is_superuser=True).exists():
            superuser=User.objects.create_superuser(
                username='admin',
                email='admin@wokkahlearn.com',
                password='admin123',
                first_name='System',
                last_name='Administrator'
            )
            superuser.total_study_time = timedelta(0)
            superuser.save()
            self.stdout.write(self.style.SUCCESS('Created superuser: admin/admin123'))
        
        # Create course categories
        categories = [
            {'name': 'Python Programming', 'icon': 'python', 'color': '#3776ab'},
            {'name': 'JavaScript', 'icon': 'javascript', 'color': '#f7df1e'},
            {'name': 'Java', 'icon': 'java', 'color': '#ed8b00'},
            {'name': 'Data Science', 'icon': 'chart-line', 'color': '#ff6b6b'},
            {'name': 'Web Development', 'icon': 'globe', 'color': '#4ecdc4'},
            {'name': 'Machine Learning', 'icon': 'brain', 'color': '#a8e6cf'},
            {'name': 'Mobile Development', 'icon': 'mobile', 'color': '#ffd93d'},
            {'name': 'DevOps', 'icon': 'cogs', 'color': '#6c5ce7'},
        ]
        
        for i, cat_data in enumerate(categories):
            category, created = CourseCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': f"Learn {cat_data['name']} from basics to advanced",
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                    'order': i + 1
                }
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Create execution environments
        environments = [
            {
                'name': 'Python 3.11',
                'language': 'python',
                'version': '3.11',
                'docker_image': 'python:3.11-alpine',
                'file_extension': '.py',
                'interpreter_command': 'python',
                'installed_packages': ['numpy', 'pandas', 'matplotlib', 'requests'],
                'is_default': True
            },
            {
                'name': 'Node.js 18',
                'language': 'javascript',
                'version': '18',
                'docker_image': 'node:18-alpine',
                'file_extension': '.js',
                'interpreter_command': 'node',
                'installed_packages': ['lodash', 'axios', 'moment'],
                'is_default': False
            },
            {
                'name': 'Java 17',
                'language': 'java',
                'version': '17',
                'docker_image': 'openjdk:17-alpine',
                'file_extension': '.java',
                'compiler_command': 'javac',
                'installed_packages': [],
                'is_default': False
            },
            {
                'name': 'C++ GCC',
                'language': 'cpp',
                'version': '11',
                'docker_image': 'gcc:11-alpine',
                'file_extension': '.cpp',
                'compiler_command': 'g++',
                'installed_packages': [],
                'is_default': False
            }
        ]
        
        for env_data in environments:
            env, created = ExecutionEnvironment.objects.get_or_create(
                language=env_data['language'],
                version=env_data['version'],
                defaults=env_data
            )
            if created:
                self.stdout.write(f'Created execution environment: {env.name}')
        
        # Create AI models
        ai_models = [
            {
                'name': 'GPT-4 Tutor',
                'model_type': 'tutor',
                'provider': 'openai',
                'model_id': 'gpt-4',
                'supports_code': True,
                'programming_languages': ['python', 'javascript', 'java', 'cpp', 'html', 'css'],
                'is_default': True
            },
            {
                'name': 'Claude Code Assistant',
                'model_type': 'code_assistant',
                'provider': 'anthropic',
                'model_id': 'claude-3-sonnet',
                'supports_code': True,
                'programming_languages': ['python', 'javascript', 'java', 'cpp'],
                'is_default': False
            },
            {
                'name': 'GPT-3.5 Explainer',
                'model_type': 'explainer',
                'provider': 'openai',
                'model_id': 'gpt-3.5-turbo',
                'supports_code': True,
                'programming_languages': ['python', 'javascript'],
                'is_default': False
            }
        ]
        
        for model_data in ai_models:
            model, created = AIModel.objects.get_or_create(
                name=model_data['name'],
                defaults=model_data
            )
            if created:
                self.stdout.write(f'Created AI model: {model.name}')
        
        # Create sample organization
        org, created = Organization.objects.get_or_create(
            name='WokkahLearn Academy',
            defaults={
                'slug': 'wokkahlearn-academy',
                'org_type': 'school',
                'description': 'Default organization for WokkahLearn platform',
                'contact_email': 'contact@wokkahlearn.com',
                'domain_whitelist': ['wokkahlearn.com'],
                'subscription_tier': 'enterprise'
            }
        )
        if created:
            self.stdout.write(f'Created organization: {org.name}')
        
        self.stdout.write(self.style.SUCCESS('Initial data setup completed!'))