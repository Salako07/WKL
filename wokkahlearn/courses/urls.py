from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseCategoryViewSet, CourseViewSet, ModuleViewSet, 
    LessonViewSet, ExerciseViewSet, CourseEnrollmentViewSet
)

router = DefaultRouter()
router.register(r'categories', CourseCategoryViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'modules', ModuleViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'exercises', ExerciseViewSet)
router.register(r'enrollments', CourseEnrollmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
