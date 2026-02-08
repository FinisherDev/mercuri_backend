import uuid

from django.db import models
from django.db.models import Index
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _

from .managers import CustomUserManager

ROLE_CHOICES = [
    ('customer', 'Customer'),
    ('rider', 'Rider'),
]
BANK_LIST = [
    ('access', 'Access Bank'),
    ('eco', 'Ecobank'),
    ('fcmb', 'FCMB'),
    ('fidelity', 'Fidelity Bank'),
    ('first', 'First Bank'),
    ('gtb', 'Guarantee Trust Bank'),
    ('heritage', 'Heritage Bank'),
    ('keystone', 'Keystone Bank'),
    ('polaris', 'Polaris Bank'),
    ('parallex', 'Parallex Bank'),
    ('stanbic', 'Stanbic IBTC Bank'),
    ('union', 'Union Bank'),
    ('uba', 'United Bank of Africa'),
    ('wema', 'Wema Bank'),
    ('zenith', 'Zenith Bank'),
]
# Create your models here.

class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    phone_number = models.CharField(max_length=11)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'role']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def is_rider(self):
        return self.role == 'rider'

    def is_customer(self):
        return self.role == 'customer'

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    class Meta:
        indexes = [
            Index(fields = ['email', 'role', ]),
        ]
        
class CustomerProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatar', blank=True)
    home_address = models.TextField(null=True)

    def __str__(self):
        return self.user.first_name

class RiderProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    middle_name = models.CharField("middle name", max_length=150, blank=True)
    profile_photo = models.ImageField(upload_to='profile', blank=True)
    driver_license = models.ImageField(upload_to='license', blank=True)
    bank_account = models.CharField(max_length=11)
    bank = models.CharField(max_length=20, choices=BANK_LIST)
    plate_number = models.CharField(max_length=11)
    brand_of_vehicle = models.CharField(max_length=15)
    colour = models.CharField(max_length=15)

    def __str__(self):
        return self.user.first_name