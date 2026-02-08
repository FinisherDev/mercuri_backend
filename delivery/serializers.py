from rest_framework import serializers
#from geopy.geocoders import Nominatim
from .models import Order, Offer

class OrderSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(read_only = True, default = serializers.CurrentUserDefault())
    driver = serializers.PrimaryKeyRelatedField(read_only = True, default = serializers.CurrentUserDefault())

    class Meta:
        model = Order
        fields = '__all__'

class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        exclude = ['customer', 'status', 'rider', 'accepted_at', 'delivered_at', 'delivery_photo']

    def create(self, validated_data):
        order = Order.objects.create(
            **validated_data,
            status = 'pending',
        )
        return order
    
class OfferSerializer(serializers.ModelSerializer):
    rider_id = serializers.PrimaryKeyRelatedField(source="driver", read_only=True)

    class Meta:
        model = Offer
        fields = ("id", "ride", "rider_id", "is_counter", "accepted", "created_at", "expire_at")
        read_only_fields = ("id", "created_at")