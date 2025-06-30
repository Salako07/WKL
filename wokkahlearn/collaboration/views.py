# collaboration/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import (
    CollaborationRoom, RoomParticipant, SharedCodeSession,
    CodeChange, HelpRequest, ChatMessage
)
from .serializers import (
    CollaborationRoomSerializer, RoomParticipantSerializer,
    SharedCodeSessionSerializer, CodeChangeSerializer,
    HelpRequestSerializer, ChatMessageSerializer
)

User = get_user_model()


class CollaborationRoomViewSet(viewsets.ModelViewSet):
    """API endpoints for collaboration rooms"""
    serializer_class = CollaborationRoomSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return CollaborationRoom.objects.filter(
            Q(creator=user) | 
            Q(participants__user=user) | 
            Q(is_public=True, status='active')
        ).distinct().order_by('-created_at')
    
    def perform_create(self, serializer):
        room = serializer.save(creator=self.request.user)
        
        # Auto-add creator as participant with moderator role
        RoomParticipant.objects.create(
            room=room,
            user=self.request.user,
            role='moderator',
            can_edit_code=True,
            can_execute_code=True,
            can_share_screen=True,
            can_moderate=True
        )
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a collaboration room"""
        room = self.get_object()
        
        # Check if room is full
        if room.max_participants:
            current_participants = room.participants.filter(status='active').count()
            if current_participants >= room.max_participants:
                return Response(
                    {'error': 'Room is full'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Check if user is already in the room
        existing_participant = room.participants.filter(user=request.user).first()
        
        if existing_participant:
            if existing_participant.status == 'left':
                # Re-join if previously left
                existing_participant.status = 'active'
                existing_participant.joined_at = timezone.now()
                existing_participant.save()
                
                return Response({
                    'message': 'Successfully rejoined room',
                    'participant': RoomParticipantSerializer(existing_participant).data
                })
            else:
                return Response(
                    {'message': 'Already in this room'},
                    status=status.HTTP_200_OK
                )
        
        # Create new participant
        participant = RoomParticipant.objects.create(
            room=room,
            user=request.user,
            role='participant',
            can_edit_code=room.room_type != 'mentor_session',  # Restrict for mentor sessions
            can_execute_code=True
        )
        
        # Update room participant count
        room.participant_count = room.participants.filter(status='active').count()
        room.save()
        
        return Response({
            'message': 'Successfully joined room',
            'participant': RoomParticipantSerializer(participant).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a collaboration room"""
        room = self.get_object()
        
        try:
            participant = room.participants.get(user=request.user)
            participant.status = 'left'
            participant.left_at = timezone.now()
            participant.save()
            
            # Update room participant count
            room.participant_count = room.participants.filter(status='active').count()
            room.save()
            
            return Response({'message': 'Successfully left room'})
        except RoomParticipant.DoesNotExist:
            return Response(
                {'error': 'Not a participant in this room'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        """Get room participants"""
        room = self.get_object()
        participants = room.participants.filter(status='active').order_by('joined_at')
        serializer = RoomParticipantSerializer(participants, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get chat messages for a room"""
        room = self.get_object()
        limit = int(request.query_params.get('limit', 50))
        
        messages = room.chat_messages.order_by('-created_at')[:limit]
        serializer = ChatMessageSerializer(list(reversed(messages)), many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message to the room"""
        room = self.get_object()
        
        # Check if user is a participant
        if not room.participants.filter(user=request.user, status='active').exists():
            return Response(
                {'error': 'Must be a participant to send messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message_type = request.data.get('message_type', 'text')
        content = request.data.get('content', '')
        metadata = request.data.get('metadata', {})
        
        if not content.strip():
            return Response(
                {'error': 'Message content cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message = ChatMessage.objects.create(
            room=room,
            sender=request.user,
            message_type=message_type,
            content=content,
            metadata=metadata
        )
        
        # Update participant message count
        participant = room.participants.get(user=request.user)
        participant.messages_sent += 1
        participant.save()
        
        # Update room total messages
        room.total_messages += 1
        room.save()
        
        serializer = ChatMessageSerializer(message, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def code_sessions(self, request, pk=None):
        """Get shared code sessions for the room"""
        room = self.get_object()
        sessions = room.code_sessions.filter(is_active=True).order_by('-updated_at')
        serializer = SharedCodeSessionSerializer(sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def create_code_session(self, request, pk=None):
        """Create a new shared code session"""
        room = self.get_object()
        
        # Check if user can create sessions (moderators only for some room types)
        participant = room.participants.filter(user=request.user, status='active').first()
        if not participant:
            return Response(
                {'error': 'Must be a participant'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        title = request.data.get('title', f'Code Session {timezone.now().strftime("%H:%M")}')
        programming_language = request.data.get('programming_language', 'python')
        initial_code = request.data.get('initial_code', '')
        
        session = SharedCodeSession.objects.create(
            room=room,
            title=title,
            programming_language=programming_language,
            current_code=initial_code,
            initial_code=initial_code,
            last_editor=request.user
        )
        
        serializer = SharedCodeSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def my_rooms(self, request):
        """Get user's rooms (created, participating, or invited)"""
        user = request.user
        rooms = CollaborationRoom.objects.filter(
            Q(creator=user) | Q(participants__user=user)
        ).distinct().order_by('-updated_at')
        
        serializer = self.get_serializer(rooms, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def public_rooms(self, request):
        """Get public rooms available to join"""
        rooms = CollaborationRoom.objects.filter(
            is_public=True,
            status='active'
        ).order_by('-created_at')
        
        serializer = self.get_serializer(rooms, many=True)
        return Response(serializer.data)


class RoomParticipantViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for room participants"""
    serializer_class = RoomParticipantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return RoomParticipant.objects.filter(
            Q(user=self.request.user) |
            Q(room__participants__user=self.request.user)
        ).distinct()
    
    @action(detail=True, methods=['post'])
    def update_permissions(self, request, pk=None):
        """Update participant permissions (moderators only)"""
        participant = self.get_object()
        room = participant.room
        
        # Check if requester is a moderator
        requester_participant = room.participants.filter(
            user=request.user,
            can_moderate=True,
            status='active'
        ).first()
        
        if not requester_participant:
            return Response(
                {'error': 'Only moderators can update permissions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update permissions
        permissions = request.data.get('permissions', {})
        for permission, value in permissions.items():
            if hasattr(participant, permission):
                setattr(participant, permission, value)
        
        participant.save()
        
        serializer = self.get_serializer(participant)
        return Response(serializer.data)


class SharedCodeSessionViewSet(viewsets.ModelViewSet):
    """API endpoints for shared code sessions"""
    serializer_class = SharedCodeSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only show sessions from rooms user participates in
        user_rooms = CollaborationRoom.objects.filter(
            participants__user=self.request.user
        )
        return SharedCodeSession.objects.filter(room__in=user_rooms)
    
    @action(detail=True, methods=['post'])
    def update_code(self, request, pk=None):
        """Update the shared code"""
        session = self.get_object()
        
        # Check if user can edit
        participant = session.room.participants.filter(
            user=request.user,
            status='active'
        ).first()
        
        if not participant or not participant.can_edit_code:
            return Response(
                {'error': 'No permission to edit code'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_code = request.data.get('code', '')
        change_type = request.data.get('change_type', 'replace')
        
        # Create code change record
        CodeChange.objects.create(
            session=session,
            user=request.user,
            change_type=change_type,
            old_text=session.current_code,
            new_text=new_code,
            version_before=session.version,
            version_after=session.version + 1,
            start_line=request.data.get('start_line', 0),
            start_column=request.data.get('start_column', 0),
            end_line=request.data.get('end_line', 0),
            end_column=request.data.get('end_column', 0)
        )
        
        # Update session
        session.current_code = new_code
        session.version += 1
        session.last_editor = request.user
        session.save()
        
        # Update participant stats
        participant.code_changes += 1
        participant.save()
        
        return Response({
            'message': 'Code updated successfully',
            'version': session.version,
            'session': SharedCodeSessionSerializer(session).data
        })
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get code change history"""
        session = self.get_object()
        changes = session.code_changes.order_by('-created_at')[:20]
        serializer = CodeChangeSerializer(changes, many=True)
        return Response(serializer.data)


class HelpRequestViewSet(viewsets.ModelViewSet):
    """API endpoints for help requests"""
    serializer_class = HelpRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Show requests user created or can help with
        return HelpRequest.objects.filter(
            Q(requester=user) |
            Q(room__participants__user=user, room__participants__can_moderate=True)
        ).distinct().order_by('-priority', '-created_at')
    
    def perform_create(self, serializer):
        room_id = self.request.data.get('room_id')
        room = get_object_or_404(CollaborationRoom, id=room_id)
        
        # Check if user is in the room
        if not room.participants.filter(user=self.request.user, status='active').exists():
            return Response(
                {'error': 'Must be in the room to request help'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer.save(
            requester=self.request.user,
            room=room
        )
    
    @action(detail=True, methods=['post'])
    def assign_helper(self, request, pk=None):
        """Assign a helper to the request"""
        help_request = self.get_object()
        helper_id = request.data.get('helper_id')
        
        # Check if requester can assign helpers (moderators)
        room = help_request.room
        participant = room.participants.filter(
            user=request.user,
            can_moderate=True,
            status='active'
        ).first()
        
        if not participant and help_request.requester != request.user:
            return Response(
                {'error': 'Only moderators or requester can assign helpers'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if helper_id:
            helper = get_object_or_404(User, id=helper_id)
            help_request.helper = helper
            help_request.status = 'in_progress'
            help_request.assigned_at = timezone.now()
        else:
            help_request.helper = None
            help_request.status = 'open'
            help_request.assigned_at = None
        
        help_request.save()
        
        serializer = self.get_serializer(help_request)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark help request as resolved"""
        help_request = self.get_object()
        
        # Only helper or requester can resolve
        if request.user not in [help_request.helper, help_request.requester]:
            return Response(
                {'error': 'Only helper or requester can resolve'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        help_request.status = 'resolved'
        help_request.resolved_at = timezone.now()
        help_request.resolution = request.data.get('resolution', '')
        help_request.resolution_code = request.data.get('resolution_code', '')
        help_request.save()
        
        return Response({'message': 'Help request resolved'})
    
    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """Rate the help received"""
        help_request = self.get_object()
        
        if request.user != help_request.requester:
            return Response(
                {'error': 'Only requester can rate'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        rating = request.data.get('rating')
        if not rating or not (1 <= int(rating) <= 5):
            return Response(
                {'error': 'Rating must be between 1 and 5'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        help_request.helpful_rating = int(rating)
        help_request.save()
        
        return Response({'message': 'Rating submitted'})
    
    @action(detail=False, methods=['get'])
    def open_requests(self, request):
        """Get open help requests that user can help with"""
        user_rooms = CollaborationRoom.objects.filter(
            participants__user=request.user,
            participants__status='active'
        )
        
        requests = HelpRequest.objects.filter(
            room__in=user_rooms,
            status='open'
        ).exclude(requester=request.user).order_by('-priority', '-created_at')
        
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)


class ChatMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for chat messages"""
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only show messages from rooms user participates in
        user_rooms = CollaborationRoom.objects.filter(
            participants__user=self.request.user
        )
        return ChatMessage.objects.filter(room__in=user_rooms).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """Add reaction to a message"""
        message = self.get_object()
        emoji = request.data.get('emoji', '👍')
        
        # Add user to reaction list
        if emoji not in message.reactions:
            message.reactions[emoji] = []
        
        user_id = str(request.user.id)
        if user_id not in message.reactions[emoji]:
            message.reactions[emoji].append(user_id)
        else:
            # Remove reaction if already exists
            message.reactions[emoji].remove(user_id)
            if not message.reactions[emoji]:
                del message.reactions[emoji]
        
        message.save()
        
        serializer = self.get_serializer(message, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        """Pin/unpin a message (moderators only)"""
        message = self.get_object()
        
        # Check if user can moderate
        participant = message.room.participants.filter(
            user=request.user,
            can_moderate=True,
            status='active'
        ).first()
        
        if not participant:
            return Response(
                {'error': 'Only moderators can pin messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.is_pinned = not message.is_pinned
        message.save()
        
        action = 'pinned' if message.is_pinned else 'unpinned'
        return Response({'message': f'Message {action} successfully'})