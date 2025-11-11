from django.db import models
from django.conf import settings
import uuid


class CallSession(models.Model):
    """Represents a single Agora channel audio call session."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel_name = models.CharField(max_length=128, unique=True)
    host = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='hosted_calls', on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)


    def mark_ended(self):
        from django.utils import timezone
        self.ended_at = timezone.now()
        self.save()


class Participant(models.Model):
    session = models.ForeignKey(CallSession, related_name='participants', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='call_participations', on_delete=models.CASCADE)
    uid = models.BigIntegerField(null=True, blank=True, help_text='Numeric Agora UID if used')
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)


    class Meta:
        unique_together = ('session', 'user')