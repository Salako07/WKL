"""
Django management command to create test data
Usage: python manage.py setup_test_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import CourseCategory, Course, Module, Lesson, Exercise
from code_execution.models import ExecutionEnvironment
from collaboration.models import CollaborationRoom
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Set up test data for WokkahLearn'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Setting up test data...')
        
        # Create test users
        self.create_test_users()
        
        # Create execution environments
        self.create_execution_environments()
        
        # Create course categories
        self.create_course_categories()
        
        # Create sample course
        self.create_sample_course()
        
        # Create collaboration room
        self.create_collaboration_room()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Test data setup completed!')
        )
    
    def create_test_users(self):
        """Create test users with different roles"""
        users_data = [
            {
                'username': 'instructor1',
                'email': 'instructor@wokkahlearn.com',
                'first_name': 'John',
                'last_name': 'Teacher',
                'role': 'instructor',
                'password': 'instructor123'
            },
            {
                'username': 'student1',
                'email': 'student@wokkahlearn.com',
                'first_name': 'Jane',
                'last_name': 'Student',
                'role': 'student',
                'password': 'student123'
            },
            {
                'username': 'mentor1',
                'email': 'mentor@wokkahlearn.com',
                'first_name': 'Bob',
                'last_name': 'Mentor',
                'role': 'mentor',
                'password': 'mentor123'
            }
        ]
        
        for user_data in users_data:
            password = user_data.pop('password')
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f'✅ Created user: {user.username}')
    
    def create_execution_environments(self):
        """Create code execution environments"""
        environments = [
            {
                'name': 'Python 3.11',
                'language': 'python',
                'version': '3.11',
                'docker_image': 'python:3.11-alpine',
                'file_extension': '.py',
                'interpreter_command': 'python',
                'is_default': True
            },
            {
                'name': 'JavaScript Node 18',
                'language': 'javascript',
                'version': '18',
                'docker_image': 'node:18-alpine',
                'file_extension': '.js',
                'interpreter_command': 'node'
            }
        ]
        
        for env_data in environments:
            env, created = ExecutionEnvironment.objects.get_or_create(
                language=env_data['language'],
                version=env_data['version'],
                defaults=env_data
            )
            if created:
                self.stdout.write(f'✅ Created environment: {env.name}')
    
    def create_course_categories(self):
        """Create course categories"""
        categories = [
            {
                'name': 'Python Programming',
                'description': 'Learn Python from basics to advanced',
                'icon': 'python',
                'color': '#3776ab'
            },
            {
                'name': 'Web Development',
                'description': 'Build modern web applications',
                'icon': 'globe',
                'color': '#61dafb'
            }
        ]
        
        for cat_data in categories:
            category, created = CourseCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'✅ Created category: {category.name}')
    
    def create_sample_course(self):
        """Create a sample course with lessons and exercises"""
        instructor = User.objects.get(username='instructor1')
        category = CourseCategory.objects.get(name='Python Programming')
        
        course, created = Course.objects.get_or_create(
            title='Python Fundamentals',
            defaults={
                'instructor': instructor,
                'category': category,
                'description': 'Learn Python programming from scratch',
                'short_description': 'Complete Python course for beginners',
                'difficulty_level': 'beginner',
                'status': 'published',
                'estimated_duration': timedelta(hours=40),
                'is_free': True,
                'learning_objectives': ['Learn Python syntax', 'Build projects'],
                'skills_gained': ['Python', 'Programming']
            }
        )
        
        if created:
            self.stdout.write(f'✅ Created course: {course.title}')
            
            # Create module
            module = Module.objects.create(
                course=course,
                title='Python Basics',
                description='Learn the fundamentals of Python',
                order=1,
                estimated_duration=timedelta(hours=10)
            )
            
            # Create lesson
            lesson = Lesson.objects.create(
                module=module,
                title='Variables and Data Types',
                lesson_type='text',
                content='# Variables in Python\n\nPython variables are containers for storing data...',
                order=1,
                estimated_duration=timedelta(minutes=30)
            )
            
            # Create exercise
            Exercise.objects.create(
                lesson=lesson,
                title='Create Your First Variables',
                exercise_type='coding',
                description='Create variables of different data types',
                starter_code='# Create variables here\nname = \nage = \n',
                solution_code='name = "John"\nage = 25\nprint(f"Name: {name}, Age: {age}")',
                programming_language='python',
                order=1,
                points=10
            )
            
            self.stdout.write(f'✅ Created module, lesson, and exercise')
    
    def create_collaboration_room(self):
        """Create a sample collaboration room"""
        creator = User.objects.get(username='instructor1')
        
        room, created = CollaborationRoom.objects.get_or_create(
            title='Python Study Group',
            defaults={
                'creator': creator,
                'description': 'Collaborative Python learning session',
                'room_type': 'study_group',
                'is_public': True,
                'max_participants': 10,
                'allow_screen_sharing': True,
                'allow_code_execution': True
            }
        )
        
        if created:
            self.stdout.write(f'✅ Created collaboration room: {room.title}')
            self.stdout.write(f'   Room code: {room.room_code}')