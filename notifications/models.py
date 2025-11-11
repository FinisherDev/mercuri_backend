from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

PLATFORMS = [
    ('android', 'Android'),
    ('ios', 'IOS'),
    ('web', 'Web'),
]

# Create your models here.
User = get_user_model()

class Device(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE, related_name = "devices")
    token = models.CharField(max_length = 255, unique = True)
    platform = models.CharField(max_length = 16, choices = PLATFORMS)
    last_seen = models.DateTimeField(default = timezone.now)

    def __str__(self):
        return f"{self.user} - {self.platform}"