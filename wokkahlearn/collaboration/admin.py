# collaboration/admin.py
from django.contrib import admin
from .models import (
    CollaborationRoom, RoomParticipant, SharedCodeSession, 
    CodeChange, HelpRequest, ChatMessage
)

@admin.register(CollaborationRoom)
class CollaborationRoomAdmin(admin.ModelAdmin):
    list_display = ('title', 'room_type', 'status', 'creator', 'participant_count', 'is_public', 'created_at')
    list_filter = ('room_type', 'status', 'is_public', 'allow_screen_sharing', 'allow_voice_chat')
    search_fields = ('title', 'description', 'room_code', 'creator__username')
    filter_horizontal = ('moderators',)

@admin.register(RoomParticipant)
class RoomParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'role', 'status', 'messages_sent', 'joined_at')
    list_filter = ('role', 'status', 'can_edit_code', 'can_execute_code')
    search_fields = ('user__username', 'room__title')

@admin.register(HelpRequest)
class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ('requester', 'room', 'request_type', 'status', 'priority', 'created_at')
    list_filter = ('request_type', 'status', 'priority')
    search_fields = ('requester__username', 'title', 'description')