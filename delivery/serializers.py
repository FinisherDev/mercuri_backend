from rest_framework import serializers
from geopy.geocoders import Nominatim
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(read_only = True, default = serializers.CurrentUserDefault())
    driver = serializers.PrimaryKeyRelatedField(read_only = True, default = serializers.CurrentUserDefault())

    class Meta:
        model = Order
        fields = '__all__'

class OrderCreateSerializer(serializers.ModelSerializer):
    pickupAddress = serializers.JSONField()
    dropoffAddress = serializers.JSONField()
    packageDetails = serializers.JSONField()
    class Meta:
        model = Order
        exclude = ['driver', 'accepted_at', 'delivered_at', 'delivery_photo']

    def create(self, validated_data):
        pickup = validated_data.pop('pickupAddress')
        dropoff = validated_data.pop('dropoffAddress')
        package = validated_data.pop('packageDetails')

        geolocator = Nominatim(user_agent="delivery_app")
        pickup_location = geolocator.geocode(f"{pickup['street']}, {pickup['city']}, {pickup['state']}")
        dropoff_location = geolocator.geocode(f"{dropoff['street']}, {dropoff['city']}, {dropoff['state']}")
        
        if pickup_location and dropoff_location:
            pickup['latitude'] = pickup_location.latitude
            pickup['longitude'] = pickup_location.longitude
            dropoff['latitude'] = dropoff_location.latitude
            dropoff['longitude'] = dropoff_location.longitude

        order = Order.objects.create(
            pickup_latitude = pickup['latitude'],
            pickup_longitude = pickup['longitude'],
            dropoff_latitude = dropoff['latitude'],
            dropoff_longitude = dropoff['longitude'],
            item_type = package['type'],
            item_category = package['category'],
            item_cost = package['value'],
            status = 'pending',
            **validated_data
        )
        return order