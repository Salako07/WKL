# ai_tutor/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AITutorSessionViewSet, AIMessageViewSet, LearningPathRecommendationViewSet,
    CodeAnalysisResultViewSet, PersonalizedQuizViewSet
)

router = DefaultRouter()
router.register(r'sessions', AITutorSessionViewSet)
router.register(r'messages', AIMessageViewSet)
router.register(r'recommendations', LearningPathRecommendationViewSet)
router.register(r'code-analysis', CodeAnalysisResultViewSet)
router.register(r'quizzes', PersonalizedQuizViewSet)

urlpatterns = [
    path('', include(router.urls)),
]