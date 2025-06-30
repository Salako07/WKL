"""from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LearningAnalyticsViewSet, StudySessionViewSet, PerformanceMetricViewSet,
    LearningInsightViewSet, CourseAnalyticsViewSet
)

router = DefaultRouter()
router.register(r'learning', LearningAnalyticsViewSet)
router.register(r'study-sessions', StudySessionViewSet)
router.register(r'performance', PerformanceMetricViewSet)
router.register(r'insights', LearningInsightViewSet)
router.register(r'course-analytics', CourseAnalyticsViewSet)

urlpatterns = [
    path('', include(router.urls)),
]"""