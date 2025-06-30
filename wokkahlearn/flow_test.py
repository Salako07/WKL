# test_api_endpoints.py
"""
Quick API testing script to verify all endpoints are working
Run this after setting up the backend to ensure everything is functional
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

def test_health_check():
    """Test health check endpoint"""
    print("🏥 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health/")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_api_documentation():
    """Test API documentation is accessible"""
    print("📚 Testing API documentation...")
    try:
        # Test schema endpoint
        schema_response = requests.get(f"{API_URL}/schema/")
        print(f"✅ Schema endpoint: {schema_response.status_code}")
        
        # Test Swagger UI
        swagger_response = requests.get(f"{API_URL}/schema/swagger-ui/")
        print(f"✅ Swagger UI: {swagger_response.status_code}")
        
        return schema_response.status_code == 200
    except Exception as e:
        print(f"❌ API documentation test failed: {e}")
        return False

def register_test_user():
    """Register a test user for API testing"""
    print("👤 Registering test user...")
    user_data = {
        "username": "testuser",
        "email": "test@wokkahlearn.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/register/", json=user_data)
        print(f"✅ User registration: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            return data.get('access'), data.get('user')
        elif response.status_code == 400:
            # User might already exist, try login
            return login_test_user()
        
        return None, None
    except Exception as e:
        print(f"❌ User registration failed: {e}")
        return None, None

def login_test_user():
    """Login with test user"""
    print("🔑 Logging in test user...")
    login_data = {
        "email": "test@wokkahlearn.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/login/", json=login_data)
        print(f"✅ User login: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            return data.get('access'), data.get('user')
        
        return None, None
    except Exception as e:
        print(f"❌ User login failed: {e}")
        return None, None

def test_protected_endpoints(token):
    """Test protected API endpoints"""
    print("🔒 Testing protected endpoints...")
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        "/courses/",
        "/ai-tutor/sessions/",
        "/collaboration/rooms/",
        "/analytics/learning/",
        "/code-execution/environments/"
    ]
    
    results = {}
    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_URL}{endpoint}", headers=headers)
            print(f"✅ {endpoint}: {response.status_code}")
            results[endpoint] = response.status_code == 200
        except Exception as e:
            print(f"❌ {endpoint} failed: {e}")
            results[endpoint] = False
    
    return results

def test_course_creation(token):
    """Test course creation flow"""
    print("📚 Testing course creation...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # First create a category
    category_data = {
        "name": "Test Programming",
        "description": "Test category for programming courses",
        "icon": "code",
        "color": "#3776ab"
    }
    
    try:
        # Create category
        cat_response = requests.post(f"{API_URL}/courses/categories/", 
                                   json=category_data, headers=headers)
        print(f"✅ Category creation: {cat_response.status_code}")
        
        if cat_response.status_code == 201:
            category_id = cat_response.json()['id']
        else:
            # Use existing category
            categories = requests.get(f"{API_URL}/courses/categories/", headers=headers)
            if categories.status_code == 200 and categories.json()['results']:
                category_id = categories.json()['results'][0]['id']
            else:
                print("❌ No categories available")
                return False
        
        # Create course
        course_data = {
            "title": "Test Python Course",
            "description": "A test course for Python programming",
            "short_description": "Learn Python basics",
            "category": category_id,
            "difficulty_level": "beginner",
            "estimated_duration": "30:00:00",
            "is_free": True,
            "learning_objectives": ["Learn Python syntax", "Write basic programs"],
            "skills_gained": ["Python", "Programming"]
        }
        
        course_response = requests.post(f"{API_URL}/courses/", 
                                      json=course_data, headers=headers)
        print(f"✅ Course creation: {course_response.status_code}")
        
        return course_response.status_code == 201
        
    except Exception as e:
        print(f"❌ Course creation failed: {e}")
        return False

def test_collaboration_features(token):
    """Test collaboration room creation"""
    print("🤝 Testing collaboration features...")
    headers = {"Authorization": f"Bearer {token}"}
    
    room_data = {
        "title": "Test Study Room",
        "description": "A test collaboration room",
        "room_type": "study_group",
        "is_public": True,
        "max_participants": 10,
        "allow_screen_sharing": True,
        "allow_voice_chat": False,
        "allow_code_execution": True
    }
    
    try:
        response = requests.post(f"{API_URL}/collaboration/rooms/", 
                               json=room_data, headers=headers)
        print(f"✅ Collaboration room creation: {response.status_code}")
        
        if response.status_code == 201:
            room_id = response.json()['id']
            
            # Test joining the room
            join_response = requests.post(f"{API_URL}/collaboration/rooms/{room_id}/join/", 
                                        headers=headers)
            print(f"✅ Room join: {join_response.status_code}")
            
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Collaboration test failed: {e}")
        return False

def run_all_tests():
    """Run comprehensive API tests"""
    print("🚀 Starting WokkahLearn API Tests")
    print("=" * 50)
    
    # Basic connectivity tests
    if not test_health_check():
        print("❌ Health check failed - server may not be running")
        return False
    
    if not test_api_documentation():
        print("❌ API documentation not accessible")
        return False
    
    # Authentication tests
    token, user = register_test_user()
    if not token:
        print("❌ Authentication failed")
        return False
    
    print(f"✅ Authenticated as: {user.get('username', 'Unknown')}")
    
    # API endpoint tests
    endpoint_results = test_protected_endpoints(token)
    failed_endpoints = [ep for ep, success in endpoint_results.items() if not success]
    
    if failed_endpoints:
        print(f"⚠️  Some endpoints failed: {failed_endpoints}")
    else:
        print("✅ All main endpoints accessible")
    
    # Feature tests
    course_test = test_course_creation(token)
    collaboration_test = test_collaboration_features(token)
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 TEST SUMMARY")
    print(f"✅ Health Check: {'PASS' if test_health_check() else 'FAIL'}")
    print(f"✅ Authentication: {'PASS' if token else 'FAIL'}")
    print(f"✅ API Endpoints: {'PASS' if not failed_endpoints else 'PARTIAL'}")
    print(f"✅ Course Creation: {'PASS' if course_test else 'FAIL'}")
    print(f"✅ Collaboration: {'PASS' if collaboration_test else 'FAIL'}")
    
    overall_success = (token and not failed_endpoints and 
                      course_test and collaboration_test)
    
    print(f"\n🎉 Overall Status: {'ALL TESTS PASSED' if overall_success else 'SOME TESTS FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    run_all_tests()


# Django management command to set up initial data
# Save as: wokkahlearn/management/commands/setup_test_data.py

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