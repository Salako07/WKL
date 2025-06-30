from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CourseViewSet, LessonViewSet, ExerciseViewSet, AITutorViewSet,
    CodeExecutionViewSet, CollaborationRoomViewSet, AnalyticsViewSet
)

router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'exercises', ExerciseViewSet)
router.register(r'ai-tutor', AITutorViewSet, basename='ai-tutor')
router.register(r'code-execution', CodeExecutionViewSet, basename='code-execution')
router.register(r'collaboration', CollaborationRoomViewSet, basename='collaboration')
router.register(r'analytics', AnalyticsViewSet, basename='analytics')

urlpatterns = [
    path('', include(router.urls)),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
