# collaboration/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    CollaborationRoom, RoomParticipant, SharedCodeSession, 
    CodeChange, HelpRequest, ChatMessage
)

User = get_user_model()


class CollaborationRoomSerializer(serializers.ModelSerializer):
    creator = serializers.StringRelatedField(read_only=True)
    participant_count = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    is_user_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = CollaborationRoom
        fields = [
            'id', 'title', 'description', 'room_type', 'status',
            'room_code', 'is_public', 'max_participants', 'creator',
            'allow_screen_sharing', 'allow_voice_chat', 'allow_file_sharing',
            'allow_code_execution', 'scheduled_start', 'scheduled_end',
            'participant_count', 'user_role', 'is_user_participant',
            'created_at'
        ]
        read_only_fields = ['id', 'room_code', 'creator', 'created_at']
    
    def get_participant_count(self, obj):
        return obj.participants.filter(status='active').count()
    
    def get_user_role(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                participant = obj.participants.get(user=request.user)
                return participant.role
            except RoomParticipant.DoesNotExist:
                if obj.creator == request.user:
                    return 'creator'
        return None
    
    def get_is_user_participant(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.participants.filter(
                user=request.user, 
                status__in=['active', 'inactive']
            ).exists()
        return False


class RoomParticipantSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    user_details = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    
    class Meta:
        model = RoomParticipant
        fields = [
            'id', 'user', 'user_details', 'role', 'status',
            'can_edit_code', 'can_execute_code', 'can_share_screen',
            'can_moderate', 'messages_sent', 'code_changes',
            'help_requests', 'last_activity', 'joined_at',
            'is_online'
        ]
        read_only_fields = ['id', 'messages_sent', 'code_changes', 'help_requests', 'joined_at']
    
    def get_user_details(self, obj):
        return {
            'id': str(obj.user.id),
            'username': obj.user.username,
            'full_name': obj.user.get_full_name(),
            'avatar': obj.user.avatar.url if obj.user.avatar else None,
            'role': obj.user.role
        }
    
    def get_is_online(self, obj):
        from datetime import timedelta
        from django.utils import timezone
        
        # Consider user online if active within last 5 minutes
        if obj.last_activity:
            return obj.last_activity > timezone.now() - timedelta(minutes=5)
        return False


class SharedCodeSessionSerializer(serializers.ModelSerializer):
    room = serializers.StringRelatedField(read_only=True)
    last_editor = serializers.StringRelatedField(read_only=True)
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = SharedCodeSession
        fields = [
            'id', 'room', 'title', 'programming_language',
            'current_code', 'initial_code', 'is_active',
            'auto_save', 'execution_enabled', 'edit_permissions',
            'version', 'last_editor', 'can_edit',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'version', 'last_editor', 'created_at', 'updated_at']
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Check edit permissions
        if obj.edit_permissions == 'all':
            return True
        elif obj.edit_permissions == 'creator':
            return obj.room.creator == user
        elif obj.edit_permissions == 'moderators':
            return (obj.room.creator == user or 
                   obj.room.participants.filter(
                       user=user, 
                       role__in=['moderator', 'presenter']
                   ).exists())
        elif obj.edit_permissions == 'presenter':
            return obj.room.participants.filter(
                user=user, 
                role='presenter'
            ).exists()
        
        return False


class CodeChangeSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    user_details = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeChange
        fields = [
            'id', 'session', 'user', 'user_details', 'change_type',
            'start_line', 'start_column', 'end_line', 'end_column',
            'old_text', 'new_text', 'operation_data',
            'version_before', 'version_after', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'version_before', 'version_after', 'created_at']
    
    def get_user_details(self, obj):
        return {
            'username': obj.user.username,
            'full_name': obj.user.get_full_name(),
            'avatar': obj.user.avatar.url if obj.user.avatar else None
        }


class HelpRequestSerializer(serializers.ModelSerializer):
    requester = serializers.StringRelatedField(read_only=True)
    helper = serializers.StringRelatedField(read_only=True)
    requester_details = serializers.SerializerMethodField()
    helper_details = serializers.SerializerMethodField()
    can_help = serializers.SerializerMethodField()
    time_elapsed = serializers.SerializerMethodField()
    
    class Meta:
        model = HelpRequest
        fields = [
            'id', 'room', 'requester', 'helper', 'requester_details',
            'helper_details', 'request_type', 'status', 'priority',
            'title', 'description', 'code_snippet', 'error_message',
            'lesson', 'exercise', 'resolution', 'resolution_code',
            'helpful_rating', 'can_help', 'time_elapsed',
            'created_at', 'assigned_at', 'resolved_at'
        ]
        read_only_fields = [
            'id', 'requester', 'requester_details', 'helper_details',
            'created_at', 'assigned_at', 'resolved_at'
        ]
    
    def get_requester_details(self, obj):
        return {
            'username': obj.requester.username,
            'full_name': obj.requester.get_full_name(),
            'avatar': obj.requester.avatar.url if obj.requester.avatar else None
        }
    
    def get_helper_details(self, obj):
        if obj.helper:
            return {
                'username': obj.helper.username,
                'full_name': obj.helper.get_full_name(),
                'avatar': obj.helper.avatar.url if obj.helper.avatar else None
            }
        return None
    
    def get_can_help(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Can't help your own request
        if obj.requester == user:
            return False
        
        # Must be in the same room
        if not obj.room.participants.filter(user=user, status='active').exists():
            return False
        
        # Request must be open
        return obj.status == 'open'
    
    def get_time_elapsed(self, obj):
        from django.utils import timezone
        
        if obj.status == 'resolved' and obj.resolved_at:
            total_time = obj.resolved_at - obj.created_at
        else:
            total_time = timezone.now() - obj.created_at
        
        return total_time.total_seconds()


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField(read_only=True)
    sender_details = serializers.SerializerMethodField()
    reply_to_details = serializers.SerializerMethodField()
    reaction_summary = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'room', 'sender', 'sender_details', 'message_type',
            'content', 'metadata', 'is_pinned', 'is_edited',
            'reply_to', 'reply_to_details', 'reactions', 'reaction_summary',
            'can_edit', 'can_delete', 'created_at', 'edited_at'
        ]
        read_only_fields = [
            'id', 'sender', 'sender_details', 'is_edited',
            'created_at', 'edited_at'
        ]
    
    def get_sender_details(self, obj):
        return {
            'username': obj.sender.username,
            'full_name': obj.sender.get_full_name(),
            'avatar': obj.sender.avatar.url if obj.sender.avatar else None,
            'role': obj.sender.role
        }
    
    def get_reply_to_details(self, obj):
        if obj.reply_to:
            return {
                'id': str(obj.reply_to.id),
                'content': obj.reply_to.content[:100] + '...' if len(obj.reply_to.content) > 100 else obj.reply_to.content,
                'sender': obj.reply_to.sender.get_full_name(),
                'created_at': obj.reply_to.created_at
            }
        return None
    
    def get_reaction_summary(self, obj):
        """Get a summary of reactions with counts"""
        if not obj.reactions:
            return {}
        
        summary = {}
        for reaction, user_ids in obj.reactions.items():
            summary[reaction] = {
                'count': len(user_ids),
                'users': user_ids  # Could be optimized to return usernames instead
            }
        return summary
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Can edit own messages within 15 minutes
        if obj.sender == user:
            from datetime import timedelta
            from django.utils import timezone
            
            edit_window = timedelta(minutes=15)
            return timezone.now() - obj.created_at < edit_window
        
        # Moderators can edit any message
        return obj.room.participants.filter(
            user=user,
            role__in=['moderator'],
            can_moderate=True
        ).exists()
    
    def get_can_delete(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Can delete own messages
        if obj.sender == user:
            return True
        
        # Room creator or moderators can delete any message
        return (obj.room.creator == user or 
               obj.room.participants.filter(
                   user=user,
                   role__in=['moderator'],
                   can_moderate=True
               ).exists())


# Nested serializers for detailed room information
class DetailedCollaborationRoomSerializer(CollaborationRoomSerializer):
    """Extended room serializer with participants and recent messages"""
    participants = RoomParticipantSerializer(many=True, read_only=True)
    recent_messages = serializers.SerializerMethodField()
    active_code_sessions = serializers.SerializerMethodField()
    open_help_requests = serializers.SerializerMethodField()
    
    class Meta(CollaborationRoomSerializer.Meta):
        fields = CollaborationRoomSerializer.Meta.fields + [
            'participants', 'recent_messages', 'active_code_sessions', 'open_help_requests'
        ]
    
    def get_recent_messages(self, obj):
        """Get last 10 messages"""
        recent = obj.chat_messages.order_by('-created_at')[:10]
        return ChatMessageSerializer(recent, many=True, context=self.context).data
    
    def get_active_code_sessions(self, obj):
        """Get active code sessions"""
        active_sessions = obj.code_sessions.filter(is_active=True)
        return SharedCodeSessionSerializer(active_sessions, many=True, context=self.context).data
    
    def get_open_help_requests(self, obj):
        """Get open help requests"""
        open_requests = obj.help_requests.filter(status='open').order_by('-priority', '-created_at')
        return HelpRequestSerializer(open_requests, many=True, context=self.context).data


# Create/Update serializers
class CreateCollaborationRoomSerializer(serializers.ModelSerializer):
    """Serializer for creating new collaboration rooms"""
    
    class Meta:
        model = CollaborationRoom
        fields = [
            'title', 'description', 'room_type', 'is_public',
            'max_participants', 'allow_screen_sharing', 'allow_voice_chat',
            'allow_file_sharing', 'allow_code_execution', 'scheduled_start',
            'scheduled_end', 'course', 'lesson', 'exercise'
        ]
    
    def create(self, validated_data):
        # Set creator from request context
        request = self.context.get('request')
        validated_data['creator'] = request.user
        return super().create(validated_data)


class CreateHelpRequestSerializer(serializers.ModelSerializer):
    """Serializer for creating help requests"""
    
    class Meta:
        model = HelpRequest
        fields = [
            'room', 'request_type', 'priority', 'title', 'description',
            'code_snippet', 'error_message', 'lesson', 'exercise'
        ]
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['requester'] = request.user
        return super().create(validated_data)


class CreateChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for creating chat messages"""
    
    class Meta:
        model = ChatMessage
        fields = ['room', 'message_type', 'content', 'metadata', 'reply_to']
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['sender'] = request.user
        return super().create(validated_data)