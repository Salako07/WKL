import pytest
from django.core.exceptions import ValidationError
from courses.models import Course, CourseEnrollment, LessonProgress


@pytest.mark.django_db
class TestCourseModels:
    
    def test_course_creation(self, course):
        assert course.title is not None
        assert course.slug is not None
        assert course.instructor is not None
        assert course.is_published
    
    def test_course_can_enroll(self, course, user):
        assert course.can_enroll(user) is True
    
    def test_course_enrollment(self, course, user):
        enrollment = CourseEnrollment.objects.create(
            student=user,
            course=course
        )
        
        assert enrollment.status == CourseEnrollment.Status.ENROLLED
        assert enrollment.progress_percentage == 0.0
        assert enrollment.lessons_completed == 0
    
    def test_enrollment_progress_update(self, course, user, lesson):
        lesson.module = course.modules.create(
            title="Test Module",
            order=1,
            estimated_duration="1:00:00"
        )
        lesson.save()
        
        enrollment = CourseEnrollment.objects.create(
            student=user,
            course=course
        )
        
        # Mark lesson as completed
        LessonProgress.objects.create(
            enrollment=enrollment,
            lesson=lesson,
            status=LessonProgress.Status.COMPLETED,
            progress_percentage=100
        )
        
        enrollment.lessons_completed = 1
        enrollment.update_progress()
        
        assert enrollment.progress_percentage > 0
    
    def test_course_slug_generation(self, instructor, course_category):
        course = Course.objects.create(
            title="Test Course With Spaces",
            instructor=instructor,
            category=course_category,
            description="Test description",
            short_description="Short desc",
            difficulty_level=Course.DifficultyLevel.BEGINNER,
            estimated_duration="30:00:00"
        )
        
        assert course.slug == "test-course-with-spaces"

