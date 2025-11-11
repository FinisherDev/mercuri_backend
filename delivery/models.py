from django.db import models
#Till further notice.  from django.contrib.gis.db import models as gis_models 
from django.contrib.auth import get_user_model
from math import radians, cos, sin, asin, sqrt

# Create your models here.

User = get_user_model()

class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    longitude = models.FloatField(default=7.0)
    latitude = models.FloatField(default=7.0)


class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined')
    ])
    item_type = models.CharField(max_length=10)
    item_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pickup_latitude = models.FloatField()
    pickup_longitude = models.FloatField()
    dropoff_latitude = models.FloatField()
    dropoff_longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add = True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    delivery_photo = models.ImageField(upload_to='delivery_photos/', null=True, blank=True)

    def is_within_radius(self, lat, lon, radius_km=3):
        """
            Checks if the pickup location is within a radius from user's lat/lon
        """
        def haversine(lat1, lon1, lat2, lon2):
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * asin(sqrt(a))
            return 6371 * c

        distance = haversine(self.pickup_latitude, self.pickup_longitude, lat, lon)
        return distance <= radius_km