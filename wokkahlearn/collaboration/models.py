# collaboration/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json

User = get_user_model()


class CollaborationRoom(models.Model):
    """Real-time collaboration rooms for coding sessions"""
    
    class RoomType(models.TextChoices):
        STUDY_GROUP = 'study_group', _('Study Group')
        LIVE_HELP = 'live_help', _('Live Help Session')
        PAIR_PROGRAMMING = 'pair_programming', _('Pair Programming')
        CODE_REVIEW = 'code_review', _('Code Review')
        MENTOR_SESSION = 'mentor_session', _('Mentor Session')
        CLASSROOM = 'classroom', _('Virtual Classroom')
        OFFICE_HOURS = 'office_hours', _('Office Hours')
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        PAUSED = 'paused', _('Paused')
        ENDED = 'ended', _('Ended')
        SCHEDULED = 'scheduled', _('Scheduled')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    room_type = models.CharField(max_length=20, choices=RoomType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    
    # Room settings
    room_code = models.CharField(max_length=20, unique=True)
    is_public = models.BooleanField(default=False)
    max_participants = models.PositiveIntegerField(default=10)
    requires_approval = models.BooleanField(default=False)
    
    # Room creator and moderators
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms')
    moderators = models.ManyToManyField(User, blank=True, related_name='moderated_rooms')
    
    # Content context
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, null=True, blank=True)
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, null=True, blank=True)
    exercise = models.ForeignKey('courses.Exercise', on_delete=models.CASCADE, null=True, blank=True)
    
    # Room features
    allow_screen_sharing = models.BooleanField(default=True)
    allow_voice_chat = models.BooleanField(default=False)
    allow_file_sharing = models.BooleanField(default=True)
    allow_code_execution = models.BooleanField(default=True)
    
    # Scheduling
    scheduled_start = models.DateTimeField(null=True, blank=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)
    
    # Session tracking
    participant_count = models.PositiveIntegerField(default=0)
    total_messages = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Collaboration Room')
        verbose_name_plural = _('Collaboration Rooms')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['room_code']),
            models.Index(fields=['status', 'room_type']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.room_code})"
    
    def save(self, *args, **kwargs):
        if not self.room_code:
            import random
            import string
            self.room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        super().save(*args, **kwargs)


class RoomParticipant(models.Model):
    """Track participants in collaboration rooms"""
    
    class Role(models.TextChoices):
        PARTICIPANT = 'participant', _('Participant')
        MODERATOR = 'moderator', _('Moderator')
        PRESENTER = 'presenter', _('Presenter')
        OBSERVER = 'observer', _('Observer')
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        KICKED = 'kicked', _('Kicked')
        LEFT = 'left', _('Left')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(CollaborationRoom, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='room_participations')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PARTICIPANT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    
    # Permissions
    can_edit_code = models.BooleanField(default=True)
    can_execute_code = models.BooleanField(default=True)
    can_share_screen = models.BooleanField(default=False)
    can_moderate = models.BooleanField(default=False)
    
    # Activity tracking
    messages_sent = models.PositiveIntegerField(default=0)
    code_changes = models.PositiveIntegerField(default=0)
    help_requests = models.PositiveIntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Room Participant')
        verbose_name_plural = _('Room Participants')
        unique_together = ['room', 'user']
        ordering = ['joined_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} in {self.room.title}"


class SharedCodeSession(models.Model):
    """Shared code editing sessions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(CollaborationRoom, on_delete=models.CASCADE, related_name='code_sessions')
    title = models.CharField(max_length=200)
    programming_language = models.CharField(max_length=50, default='python')
    
    # Code content
    current_code = models.TextField(default='')
    initial_code = models.TextField(default='')
    
    # Session settings
    is_active = models.BooleanField(default=True)
    auto_save = models.BooleanField(default=True)
    execution_enabled = models.BooleanField(default=True)
    
    # Permissions
    edit_permissions = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All Participants'),
            ('moderators', 'Moderators Only'),
            ('presenter', 'Presenter Only'),
            ('creator', 'Creator Only')
        ],
        default='all'
    )
    
    # Version tracking
    version = models.PositiveIntegerField(default=1)
    last_editor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Shared Code Session')
        verbose_name_plural = _('Shared Code Sessions')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Code Session: {self.title}"


class CodeChange(models.Model):
    """Track code changes for collaborative editing"""
    
    class ChangeType(models.TextChoices):
        INSERT = 'insert', _('Insert')
        DELETE = 'delete', _('Delete')
        REPLACE = 'replace', _('Replace')
        FORMAT = 'format', _('Format')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(SharedCodeSession, on_delete=models.CASCADE, related_name='code_changes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    change_type = models.CharField(max_length=20, choices=ChangeType.choices)
    
    # Change details
    start_line = models.PositiveIntegerField()
    start_column = models.PositiveIntegerField()
    end_line = models.PositiveIntegerField()
    end_column = models.PositiveIntegerField()
    
    # Change content
    old_text = models.TextField(blank=True)
    new_text = models.TextField(blank=True)
    
    # Operational Transform data
    operation_data = models.JSONField(default=dict)
    
    # Metadata
    version_before = models.PositiveIntegerField()
    version_after = models.PositiveIntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Code Change')
        verbose_name_plural = _('Code Changes')
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_change_type_display()}"


class HelpRequest(models.Model):
    """Help requests within collaboration rooms"""
    
    class RequestType(models.TextChoices):
        DEBUGGING = 'debugging', _('Debugging Help')
        CONCEPT = 'concept', _('Concept Explanation')
        CODE_REVIEW = 'code_review', _('Code Review')
        GENERAL = 'general', _('General Question')
        TECHNICAL = 'technical', _('Technical Issue')
    
    class Status(models.TextChoices):
        OPEN = 'open', _('Open')
        IN_PROGRESS = 'in_progress', _('In Progress')
        RESOLVED = 'resolved', _('Resolved')
        CLOSED = 'closed', _('Closed')
    
    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        URGENT = 'urgent', _('Urgent')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(CollaborationRoom, on_delete=models.CASCADE, related_name='help_requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='help_requests')
    helper = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='help_provided')
    
    request_type = models.CharField(max_length=20, choices=RequestType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    
    # Request content
    title = models.CharField(max_length=200)
    description = models.TextField()
    code_snippet = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    
    # Context
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.SET_NULL, null=True, blank=True)
    exercise = models.ForeignKey('courses.Exercise', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Resolution
    resolution = models.TextField(blank=True)
    resolution_code = models.TextField(blank=True)
    helpful_rating = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Help Request')
        verbose_name_plural = _('Help Requests')
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"Help Request: {self.title} by {self.requester.get_full_name()}"


class ChatMessage(models.Model):
    """Chat messages in collaboration rooms"""
    
    class MessageType(models.TextChoices):
        TEXT = 'text', _('Text Message')
        CODE = 'code', _('Code Snippet')
        FILE = 'file', _('File Share')
        SYSTEM = 'system', _('System Message')
        HELP_REQUEST = 'help_request', _('Help Request')
        SCREEN_SHARE = 'screen_share', _('Screen Share')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(CollaborationRoom, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=20, choices=MessageType.choices, default=MessageType.TEXT)
    
    # Message content
    content = models.TextField()
    metadata = models.JSONField(default=dict)  # Additional data like file info, code language, etc.
    
    # Message features
    is_pinned = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    # Threading
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Reactions
    reactions = models.JSONField(default=dict)  # {"👍": ["user_id1", "user_id2"], ...}
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Chat Message')
        verbose_name_plural = _('Chat Messages')
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"