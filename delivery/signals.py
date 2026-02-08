from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from .models import Rider

User = get_user_model()

# Driver Creation Logic
@receiver(post_save, sender=User)
def create_driver(sender, instance, created, **kwargs):
    if created and instance.role == 'rider':
        Rider.objects.create(user=instance)


#@receiver(post_save, sender=User)
#def save_driver(sender, instance, **kwargs):
#    instance.driver.save()