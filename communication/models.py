from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Call(models.Model):
    CALL_STATUS = (
        ('initiated', 'Initiated'),
        ('ringing', 'Ringing'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('ended', 'Ended'),
        ('missed', 'Missed'),
    )
    
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outgoing_calls')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incoming_calls')
    channel_name = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=CALL_STATUS, default='initiated')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(default=0, help_text='Duration in seconds')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Call from {self.caller.email} to {self.receiver.email}"
    
#Chat Room Models
class ChatRoom(models.Model):
    """One-on-one chat room between two users"""
    participant_1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_rooms_as_participant_1')
    participant_2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_rooms_as_participant_2')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = ('participant_1', 'participant_2')
    
    def __str__(self):
        return f"Chat: {self.participant_1.email} & {self.participant_2.email}"
    
    def get_other_participant(self, user):
        """Get the other participant in the chat"""
        if self.participant_1 == user:
            return self.participant_2
        return self.participant_1
    
    def get_unread_count(self, user):
        """Get unread message count for a user"""
        last_read = ChatRoomMembership.objects.filter(
            room=self, user=user
        ).first()
        
        if not last_read:
            return self.messages.count()
        
        return self.messages.filter(
            created_at__gt=last_read.last_read_at
        ).exclude(sender=user).count()


class ChatRoomMembership(models.Model):
    """Track user read status in rooms"""
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(default=timezone.now)
    is_muted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('room', 'user')
    
    def __str__(self):
        return f"{self.user.email} in {self.room}"


class Message(models.Model):
    MESSAGE_TYPE = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('audio', 'Audio'),
        ('file', 'File'),
    )
    
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE, default='text')
    content = models.TextField(blank=True)
    file_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    
    # Read receipts
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.email}: {self.content[:50]}"


class FCMDevice(models.Model):
    """Store FCM tokens for push notifications"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fcm_devices')
    registration_token = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(max_length=10, choices=(('ios', 'iOS'), ('android', 'Android')))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'registration_token')
    
    def __str__(self):
        return f"{self.user.email} - {self.device_type}"

