from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import Course, CourseCategory, Module, Lesson, Exercise
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample course data'

    def handle(self, *args, **options):
        # Get or create instructor
        instructor, created = User.objects.get_or_create(
            username='instructor',
            defaults={
                'email': 'instructor@wokkahlearn.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'role': 'instructor'
            }
        )
        if created:
            instructor.set_password('instructor123')
            instructor.save()
        
        # Get Python category
        try:
            category = CourseCategory.objects.get(name='Python Programming')
        except CourseCategory.DoesNotExist:
            category = CourseCategory.objects.create(
                name='Python Programming',
                description='Python programming courses'
            )
        
        # Create sample course
        course, created = Course.objects.get_or_create(
            title='Python Fundamentals',
            defaults={
                'slug': 'python-fundamentals',
                'instructor': instructor,
                'category': category,
                'description': '''Learn Python programming from scratch. This comprehensive course covers 
                                 variables, data types, control structures, functions, and basic object-oriented programming.''',
                'short_description': 'Complete Python course for beginners',
                'difficulty_level': 'beginner',
                'status': 'published',
                'estimated_duration': timedelta(hours=40),
                'is_free': True,
                'learning_objectives': [
                    'Understand Python syntax and basic programming concepts',
                    'Work with variables, data types, and operators',
                    'Use control structures like loops and conditionals',
                    'Create and use functions',
                    'Understand basic object-oriented programming'
                ],
                'skills_gained': ['Python', 'Programming Logic', 'Problem Solving'],
                'programming_languages': ['python']
            }
        )
        
        if created:
            self.stdout.write(f'Created course: {course.title}')
            
            # Create modules
            modules_data = [
                {
                    'title': 'Getting Started with Python',
                    'description': 'Introduction to Python and setting up development environment',
                    'order': 1,
                    'lessons': [
                        {
                            'title': 'What is Python?',
                            'lesson_type': 'text',
                            'content': '''# What is Python?

Python is a high-level, interpreted programming language known for its simplicity and readability. 
Created by Guido van Rossum in 1991, Python emphasizes code readability and allows programmers 
to express concepts in fewer lines of code.

## Key Features:
- **Easy to Learn**: Simple, readable syntax
- **Versatile**: Used for web development, data science, automation, and more
- **Large Community**: Extensive libraries and frameworks
- **Cross-platform**: Runs on Windows, macOS, and Linux

## Why Learn Python?
1. Beginner-friendly syntax
2. High demand in job market
3. Excellent for automation and scripting
4. Strong in data science and AI
5. Large standard library

Let's start your Python journey!'''
                        },
                        {
                            'title': 'Installing Python',
                            'lesson_type': 'text',
                            'content': '''# Installing Python

## Download Python
Visit [python.org](https://python.org) and download the latest version for your operating system.

## Installation Steps:
1. Run the installer
2. Check "Add Python to PATH"
3. Complete the installation
4. Verify installation by opening terminal/command prompt
5. Type `python --version`

## IDE Recommendations:
- **VS Code**: Free, lightweight with great Python support
- **PyCharm**: Full-featured Python IDE
- **Jupyter Notebook**: Great for data science and learning

You're ready to code!'''
                        }
                    ]
                },
                {
                    'title': 'Python Basics',
                    'description': 'Variables, data types, and basic operations',
                    'order': 2,
                    'lessons': [
                        {
                            'title': 'Variables and Data Types',
                            'lesson_type': 'text',
                            'content': '''# Variables and Data Types

## Variables
Variables are containers for storing data values. In Python, you don't need to declare variable types.

```python
# Creating variables
name = "Alice"
age = 25
height = 5.6
is_student = True
```

## Data Types:
- **int**: Whole numbers (1, 42, -10)
- **float**: Decimal numbers (3.14, -2.5)
- **str**: Text ("Hello", 'World')
- **bool**: True or False
- **list**: Ordered collection [1, 2, 3]
- **dict**: Key-value pairs {"name": "Alice"}

## Type Checking:
```python
print(type(name))      # <class 'str'>
print(type(age))       # <class 'int'>
print(type(height))    # <class 'float'>
```''',
                            'exercises': [
                                {
                                    'title': 'Create Variables',
                                    'description': '''Create variables for the following:
1. Your name (string)
2. Your age (integer) 
3. Your favorite number (float)
4. Whether you like programming (boolean)

Print all variables and their types.''',
                                    'starter_code': '''# Create your variables here
# name = 
# age = 
# favorite_number = 
# likes_programming = 

# Print variables and types
''',
                                    'solution_code': '''# Create your variables here
name = "Student"
age = 20
favorite_number = 3.14
likes_programming = True

# Print variables and types
print(f"Name: {name}, Type: {type(name)}")
print(f"Age: {age}, Type: {type(age)}")
print(f"Favorite Number: {favorite_number}, Type: {type(favorite_number)}")
print(f"Likes Programming: {likes_programming}, Type: {type(likes_programming)}")''',
                                    'programming_language': 'python',
                                    'test_cases': [
                                        {
                                            'name': 'Variables Created',
                                            'input_data': '',
                                            'expected_output': 'Name: Student, Type: <class \'str\'>',
                                            'test_type': 'output'
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
            
            for module_data in modules_data:
                module = Module.objects.create(
                    course=course,
                    title=module_data['title'],
                    description=module_data['description'],
                    order=module_data['order'],
                    estimated_duration=timedelta(hours=5)
                )
                
                for i, lesson_data in enumerate(module_data['lessons'], 1):
                    lesson = Lesson.objects.create(
                        module=module,
                        title=lesson_data['title'],
                        lesson_type=lesson_data['lesson_type'],
                        content=lesson_data['content'],
                        order=i,
                        estimated_duration=timedelta(minutes=30)
                    )
                    
                    # Create exercises if present
                    if 'exercises' in lesson_data:
                        for j, exercise_data in enumerate(lesson_data['exercises'], 1):
                            exercise = Exercise.objects.create(
                                lesson=lesson,
                                title=exercise_data['title'],
                                description=exercise_data['description'],
                                starter_code=exercise_data['starter_code'],
                                solution_code=exercise_data['solution_code'],
                                programming_language=exercise_data['programming_language'],
                                order=j,
                                points=10
                            )
                            self.stdout.write(f'  Created exercise: {exercise.title}')
                    
                    self.stdout.write(f'  Created lesson: {lesson.title}')
                
                self.stdout.write(f'Created module: {module.title}')
        
        self.stdout.write(self.style.SUCCESS('Sample course created successfully!'))
