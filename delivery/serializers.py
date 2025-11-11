from rest_framework import serializers
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(read_only = True, default = serializers.CurrentUserDefault())
    driver = serializers.PrimaryKeyRelatedField(read_only = True, default = serializers.CurrentUserDefault())

    class Meta:
        model = Order
        fields = '__all__'

class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        exclude = ['driver', 'accepted_at', 'delivered_at', 'delivery_photo']