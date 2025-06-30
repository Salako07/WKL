# collaboration/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from datetime import timedelta
from django.utils import timezone

from .models import (
    CollaborationRoom, RoomParticipant, SharedCodeSession,
    CodeChange, HelpRequest, ChatMessage
)
from .serializers import (
    CollaborationRoomSerializer, DetailedCollaborationRoomSerializer,
    CreateCollaborationRoomSerializer, RoomParticipantSerializer,
    SharedCodeSessionSerializer, CodeChangeSerializer,
    HelpRequestSerializer, CreateHelpRequestSerializer,
    ChatMessageSerializer, CreateChatMessageSerializer
)


class CollaborationRoomViewSet(viewsets.ModelViewSet):
    """API endpoints for collaboration rooms"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['room_type', 'status', 'is_public']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'participant_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        # Users can see rooms they created, joined, or public rooms
        return CollaborationRoom.objects.filter(
            Q(creator=user) | 
            Q(participants__user=user) | 
            Q(is_public=True)
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateCollaborationRoomSerializer
        elif self.action == 'retrieve':
            return DetailedCollaborationRoomSerializer
        return CollaborationRoomSerializer
    
    def perform_create(self, serializer):
        room = serializer.save(creator=self.request.user)
        
        # Automatically add creator as participant with moderator role
        RoomParticipant.objects.create(
            room=room,
            user=self.request.user,
            role='moderator',
            status='active',
            can_edit_code=True,
            can_execute_code=True,
            can_share_screen=True,
            can_moderate=True
        )
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a collaboration room"""
        room = self.get_object()
        user = request.user
        
        # Check if room allows new participants
        if not room.allow_enrollment:
            return Response(
                {'error': 'Room is not accepting new participants'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check participant limit
        if room.max_participants:
            current_count = room.participants.filter(status='active').count()
            if current_count >= room.max_participants:
                return Response(
                    {'error': 'Room is full'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Check if user is already a participant
        participant, created = RoomParticipant.objects.get_or_create(
            room=room,
            user=user,
            defaults={
                'role': 'participant',
                'status': 'active',
                'can_edit_code': True,
                'can_execute_code': True,
                'can_share_screen': False,
                'can_moderate': False
            }
        )
        
        if not created:
            # Reactivate if previously left
            if participant.status != 'active':
                participant.status = 'active'
                participant.joined_at = timezone.now()
                participant.save()
                
        # Update room participant count
        room.participant_count = room.participants.filter(status='active').count()
        room.save()
        
        serializer = RoomParticipantSerializer(participant, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a collaboration room"""
        room = self.get_object()
        user = request.user
        
        try:
            participant = room.participants.get(user=user)
            participant.status = 'left'
            participant.left_at = timezone.now()
            participant.save()
            
            # Update room participant count
            room.participant_count = room.participants.filter(status='active').count()
            room.save()
            
            return Response({'message': 'Successfully left the room'})
        except RoomParticipant.DoesNotExist:
            return Response(
                {'error': 'You are not a participant of this room'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        """Get room participants"""
        room = self.get_object()
        participants = room.participants.filter(status='active').order_by('joined_at')
        serializer = RoomParticipantSerializer(participants, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_participant_permissions(self, request, pk=None):
        """Update participant permissions (moderators only)"""
        room = self.get_object()
        user = request.user
        
        # Check if user can moderate
        if not (room.creator == user or 
               room.participants.filter(user=user, can_moderate=True).exists()):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        participant_id = request.data.get('participant_id')
        permissions = request.data.get('permissions', {})
        
        try:
            participant = room.participants.get(id=participant_id)
            
            # Update permissions
            for key, value in permissions.items():
                if hasattr(participant, key):
                    setattr(participant, key, value)
            
            participant.save()
            
            serializer = RoomParticipantSerializer(participant, context={'request': request})
            return Response(serializer.data)
            
        except RoomParticipant.DoesNotExist:
            return Response(
                {'error': 'Participant not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def end_session(self, request, pk=None):
        """End the collaboration session (creator only)"""
        room = self.get_object()
        user = request.user
        
        if room.creator != user:
            return Response(
                {'error': 'Only the room creator can end the session'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        room.status = 'ended'
        room.ended_at = timezone.now()
        room.save()
        
        # Mark all code sessions as inactive
        room.code_sessions.update(is_active=False)
        
        return Response({'message': 'Session ended successfully'})


class RoomParticipantViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for room participants"""
    serializer_class = RoomParticipantSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Users can only see participants of rooms they're part of
        return RoomParticipant.objects.filter(
            Q(room__creator=user) |
            Q(room__participants__user=user) |
            Q(room__is_public=True)
        ).distinct()


class SharedCodeSessionViewSet(viewsets.ModelViewSet):
    """API endpoints for shared code sessions"""
    serializer_class = SharedCodeSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return SharedCodeSession.objects.filter(
            Q(room__creator=user) |
            Q(room__participants__user=user)
        ).distinct()
    
    def perform_create(self, serializer):
        room_id = self.request.data.get('room_id')
        room = get_object_or_404(CollaborationRoom, id=room_id)
        
        # Check if user can create code sessions in this room
        if not (room.creator == self.request.user or 
               room.participants.filter(user=self.request.user, status='active').exists()):
            raise permissions.PermissionDenied("You must be a participant to create code sessions")
        
        serializer.save(room=room)
    
    @action(detail=True, methods=['post'])
    def update_code(self, request, pk=None):
        """Update shared code content"""
        session = self.get_object()
        user = request.user
        
        # Check edit permissions
        serializer = SharedCodeSessionSerializer(session, context={'request': request})
        if not serializer.get_can_edit(session):
            return Response(
                {'error': 'You do not have permission to edit this code'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_code = request.data.get('code', '')
        change_data = request.data.get('change', {})
        
        # Create code change record
        CodeChange.objects.create(
            session=session,
            user=user,
            change_type=change_data.get('type', 'replace'),
            start_line=change_data.get('start_line', 0),
            start_column=change_data.get('start_column', 0),
            end_line=change_data.get('end_line', 0),
            end_column=change_data.get('end_column', 0),
            old_text=session.current_code,
            new_text=new_code,
            version_before=session.version,
            version_after=session.version + 1
        )
        
        # Update session
        session.current_code = new_code
        session.version += 1
        session.last_editor = user
        session.save()
        
        return Response({
            'message': 'Code updated successfully',
            'version': session.version,
            'code': session.current_code
        })
    
    @action(detail=True, methods=['get'])
    def changes(self, request, pk=None):
        """Get code change history"""
        session = self.get_object()
        changes = session.code_changes.order_by('-created_at')[:50]
        serializer = CodeChangeSerializer(changes, many=True, context={'request': request})
        return Response(serializer.data)


class HelpRequestViewSet(viewsets.ModelViewSet):
    """API endpoints for help requests"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['request_type', 'status', 'priority']
    ordering_fields = ['created_at', 'priority']
    ordering = ['-priority', '-created_at']
    
    def get_queryset(self):
        user = self.request.user
        return HelpRequest.objects.filter(
            Q(room__creator=user) |
            Q(room__participants__user=user) |
            Q(requester=user) |
            Q(helper=user)
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateHelpRequestSerializer
        return HelpRequestSerializer
    
    def perform_create(self, serializer):
        serializer.save(requester=self.request.user)
    
    @action(detail=True, methods=['post'])
    def offer_help(self, request, pk=None):
        """Offer to help with a request"""
        help_request = self.get_object()
        user = request.user
        
        if help_request.status != 'open':
            return Response(
                {'error': 'This help request is no longer open'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if help_request.requester == user:
            return Response(
                {'error': 'You cannot help with your own request'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is in the same room
        if not help_request.room.participants.filter(user=user, status='active').exists():
            return Response(
                {'error': 'You must be in the same room to offer help'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        help_request.helper = user
        help_request.status = 'in_progress'
        help_request.assigned_at = timezone.now()
        help_request.save()
        
        return Response({'message': 'Successfully assigned to help request'})
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark help request as resolved"""
        help_request = self.get_object()
        user = request.user
        
        # Only helper or requester can resolve
        if not (help_request.helper == user or help_request.requester == user):
            return Response(
                {'error': 'Only the helper or requester can resolve this'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        resolution = request.data.get('resolution', '')
        resolution_code = request.data.get('resolution_code', '')
        rating = request.data.get('rating')
        
        help_request.status = 'resolved'
        help_request.resolution = resolution
        help_request.resolution_code = resolution_code
        help_request.resolved_at = timezone.now()
        
        if rating and 1 <= rating <= 5:
            help_request.helpful_rating = rating
        
        help_request.save()
        
        return Response({'message': 'Help request resolved successfully'})


class ChatMessageViewSet(viewsets.ModelViewSet):
    """API endpoints for chat messages"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['message_type', 'is_pinned']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        room_id = self.request.query_params.get('room_id')
        
        queryset = ChatMessage.objects.filter(
            Q(room__creator=user) |
            Q(room__participants__user=user)
        ).distinct()
        
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateChatMessageSerializer
        return ChatMessageSerializer
    
    def perform_create(self, serializer):
        room_id = self.request.data.get('room')
        room = get_object_or_404(CollaborationRoom, id=room_id)
        
        # Check if user can send messages in this room
        if not (room.creator == self.request.user or 
               room.participants.filter(user=self.request.user, status='active').exists()):
            raise permissions.PermissionDenied("You must be a participant to send messages")
        
        message = serializer.save(sender=self.request.user)
        
        # Update participant message count
        try:
            participant = room.participants.get(user=self.request.user)
            participant.messages_sent += 1
            participant.save()
        except RoomParticipant.DoesNotExist:
            pass
    
    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """Add or remove reaction to a message"""
        message = self.get_object()
        user = request.user
        reaction = request.data.get('reaction')
        
        if not reaction:
            return Response(
                {'error': 'Reaction emoji is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reactions = message.reactions or {}
        user_id = str(user.id)
        
        if reaction in reactions:
            if user_id in reactions[reaction]:
                # Remove reaction
                reactions[reaction].remove(user_id)
                if not reactions[reaction]:
                    del reactions[reaction]
                action = 'removed'
            else:
                # Add reaction
                reactions[reaction].append(user_id)
                action = 'added'
        else:
            # New reaction
            reactions[reaction] = [user_id]
            action = 'added'
        
        message.reactions = reactions
        message.save()
        
        return Response({
            'message': f'Reaction {action} successfully',
            'reactions': reactions
        })
    
    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        """Pin or unpin a message (moderators only)"""
        message = self.get_object()
        user = request.user
        
        # Check if user can pin messages
        if not (message.room.creator == user or 
               message.room.participants.filter(user=user, can_moderate=True).exists()):
            return Response(
                {'error': 'Only moderators can pin messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.is_pinned = not message.is_pinned
        message.save()
        
        action = 'pinned' if message.is_pinned else 'unpinned'
        return Response({'message': f'Message {action} successfully'})
    
    def destroy(self, request, *args, **kwargs):
        """Delete a message (with permissions check)"""
        message = self.get_object()
        
        # Use serializer to check permissions
        serializer = ChatMessageSerializer(message, context={'request': request})
        if not serializer.get_can_delete(message):
            return Response(
                {'error': 'You do not have permission to delete this message'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)