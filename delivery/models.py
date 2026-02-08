import uuid
from decimal import Decimal

from django.db import models
#Till further notice.  from django.contrib.gis.db import models as gis_models 
from django.contrib.auth import get_user_model

# Create your models here.

PACKAGE_CATEGORIES = [
  ("electronics", "Electronics"),
  ("documents", "Documents"),
  ("clothing", "Clothing"),
  ("food_and_beverages", "Food & Beverages"),
  ("fragile", "Fragile Items"),
  ("books", "Books"),
  ("others", "Others"),
]

EVENT_CHOICES = [
    ("sent", "Sent"),
    ("countered", "Countered"),
    ("accepted", "Accepted"),
    ("declined", "Declined"),
    ("expired", "Expired"),
]

User = get_user_model()

class Rider(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    longitude = models.FloatField(default=7.0)
    latitude = models.FloatField(default=7.0)
    heading = models.FloatField(null=True, blank=True)
    speed = models.FloatField(null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    idle_since = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add = True)
    location_last_updated_at = models.DateField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['longitude', 'latitude']),
            models.Index(fields=['is_available', 'location_last_updated_at'])
        ]


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    rider = models.ForeignKey(Rider, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired')
    ])
    item_type = models.CharField(max_length=10)
    item_category = models.CharField(max_length=50, choices=PACKAGE_CATEGORIES, default='other')
    suggested_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    pickup_latitude = models.FloatField()
    pickup_longitude = models.FloatField()
    dropoff_latitude = models.FloatField()
    dropoff_longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add = True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    delivery_photo = models.ImageField(upload_to='delivery_photos/', null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['customer', 'rider', 'created_at'])
        ]

class Offer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="offers")
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name="offers")
    fare = models.DecimalField(max_digits=12, decimal_places=2)
    is_counter = models.BooleanField(default=True)
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["order", "rider", "created_at"])
        ]

class OfferEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="events")
    event = models.CharField(max_length=20, choices=EVENT_CHOICES)
    payload = models.JSONField(blank=True, default=dict) 
    created_at = models.DateTimeField(auto_now_add=True)