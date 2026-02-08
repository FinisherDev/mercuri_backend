from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.dispatch import receiver
#from django.core.mail import EmailMultiAlternatives
#from django.template.loader import render_to_string
#from django.urls import reverse

#from django_rest_passwordreset.signals import reset_password_token_created

from .models import CustomerProfile, RiderProfile


User = get_user_model()

#Profile Creation Logic
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'customer':
            CustomerProfile.objects.create(user=instance)
        elif instance.role == 'rider':
            RiderProfile.objects.create(user=instance)

# Password reset
'''
@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    context = {
        'current_user': reset_password_token.user,
        'username': reset_password_token.user.username,
        'email': reset_password_token.user.email,
        'reset_password_url': "{}?token={}".format(
            instance.request.build_absolute_uri(
                reverse('password_reset:reset-password-confirm')),
            reset_password_token.key)
    }

    email_html_message = render_to_string(
        'users/user_reset_password.html', context)
    email_plaintext_message = render_to_string(
        'users/user_reset_password.txt', context)

    msg = EmailMultiAlternatives(
        # title:
        "Password Reset for {title}".format(title="Recipe app"),
        # message:
        email_plaintext_message,
        # from:
        "noreply@somehost.local",
        # to:
        [reset_password_token.user.email]
    )
    msg.attach_alternative(email_html_message, "text/html")
    msg.send()
'''