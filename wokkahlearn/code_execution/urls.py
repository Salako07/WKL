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
