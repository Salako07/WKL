from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CollaborationRoomViewSet, RoomParticipantViewSet, 
    SharedCodeSessionViewSet, HelpRequestViewSet, ChatMessageViewSet
)

router = DefaultRouter()
router.register(r'rooms', CollaborationRoomViewSet)
router.register(r'participants', RoomParticipantViewSet)
router.register(r'code-sessions', SharedCodeSessionViewSet)
router.register(r'help-requests', HelpRequestViewSet)
router.register(r'messages', ChatMessageViewSet)

urlpatterns = [
    path('', include(router.urls)),
]