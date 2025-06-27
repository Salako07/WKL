import pytest
from django.urls import reverse
from rest_framework import status
from courses.models import Course, CourseEnrollment


@pytest.mark.django_db
class TestCoursesAPI:
    
    def test_list_courses(self, api_client, course):
        url = reverse('course-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == course.title
    
    def test_course_detail(self, api_client, course):
        url = reverse('course-detail', kwargs={'pk': course.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == course.title
        assert response.data['instructor']['id'] == str(course.instructor.id)
    
    def test_enroll_in_course(self, authenticated_client, course, user):
        url = reverse('course-enroll', kwargs={'pk': course.id})
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert CourseEnrollment.objects.filter(student=user, course=course).exists()
    
    def test_enroll_twice_same_course(self, authenticated_client, course, user):
        # First enrollment
        url = reverse('course-enroll', kwargs={'pk': course.id})
        authenticated_client.post(url)
        
        # Second enrollment attempt
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert CourseEnrollment.objects.filter(student=user, course=course).count() == 1
    
    def test_course_modules(self, authenticated_client, course):
        url = reverse('course-modules', kwargs={'pk': course.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
    
    def test_filter_courses_by_difficulty(self, api_client, course):
        url = reverse('course-list')
        response = api_client.get(url, {'difficulty_level': 'beginner'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
    
    def test_search_courses(self, api_client, course):
        url = reverse('course-list')
        response = api_client.get(url, {'search': course.title.split()[0]})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

