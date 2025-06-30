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



# code_execution/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ExecutionEnvironmentViewSet, CodeExecutionViewSet, 
    TestCaseViewSet, CodePlaygroundViewSet
)

router = DefaultRouter()
router.register(r'environments', ExecutionEnvironmentViewSet)
router.register(r'executions', CodeExecutionViewSet)
router.register(r'test-cases', TestCaseViewSet)
router.register(r'playground', CodePlaygroundViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
