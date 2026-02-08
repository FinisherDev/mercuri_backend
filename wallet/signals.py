from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from .models import Wallet

User = get_user_model()

# Wallet Creation Logic
@receiver(post_save, sender=User)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_wallet(sender, instance, **kwargs):
    instance.wallet.save()