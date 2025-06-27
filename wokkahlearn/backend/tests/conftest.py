# backend/tests/conftest.py
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import factory
from faker import Faker

from courses.models import Course, CourseCategory, Lesson, Exercise
from accounts.models import UserProfile

User = get_user_model()
fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    role = User.Role.STUDENT


class InstructorFactory(UserFactory):
    role = User.Role.INSTRUCTOR


class CourseCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CourseCategory
    
    name = factory.Faker('word')
    slug = factory.LazyAttribute(lambda obj: obj.name.lower())
    description = factory.Faker('text', max_nb_chars=200)


class CourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Course
    
    title = factory.Faker('sentence', nb_words=4)
    slug = factory.LazyAttribute(lambda obj: obj.title.lower().replace(' ', '-'))
    description = factory.Faker('text', max_nb_chars=500)
    short_description = factory.Faker('text', max_nb_chars=100)
    instructor = factory.SubFactory(InstructorFactory)
    category = factory.SubFactory(CourseCategoryFactory)
    difficulty_level = Course.DifficultyLevel.BEGINNER
    status = Course.Status.PUBLISHED
    estimated_duration = factory.Faker('time_delta', end_datetime='+30d')
    is_free = True


class LessonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Lesson
    
    title = factory.Faker('sentence', nb_words=3)
    slug = factory.LazyAttribute(lambda obj: obj.title.lower().replace(' ', '-'))
    lesson_type = Lesson.LessonType.TEXT
    description = factory.Faker('text', max_nb_chars=200)
    content = factory.Faker('text', max_nb_chars=1000)
    order = factory.Sequence(lambda n: n)
    estimated_duration = factory.Faker('time_delta', end_datetime='+2h')


class ExerciseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Exercise
    
    title = factory.Faker('sentence', nb_words=3)
    exercise_type = Exercise.ExerciseType.CODING
    difficulty = Exercise.Difficulty.EASY
    description = factory.Faker('text', max_nb_chars=500)
    starter_code = "# Write your code here"
    solution_code = "print('Hello, World!')"
    programming_language = "python"
    points = 10


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def instructor():
    return InstructorFactory()


@pytest.fixture
def course():
    return CourseFactory()


@pytest.fixture
def lesson():
    return LessonFactory()


@pytest.fixture
def exercise():
    return ExerciseFactory()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def instructor_client(instructor):
    client = APIClient()
    refresh = RefreshToken.for_user(instructor)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client

