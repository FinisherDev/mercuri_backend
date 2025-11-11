from django.shortcuts import render
from django.utils import timezone
from rest_framework import viewsets, permissions
from .models import Device
from .serializers import DeviceSerializer

# Create your views here.

class DeviceViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        return Device.objects.filter(user = self.request.user)
    
    def perform_create(self, serializer):
        token = serializer.validated_data['token']
        platform = serializer.validated_data['platform']
        obj, _ = Device.objects.update_or_create(
            token = token,
            defaults = {'user': self.request.user, 'platform': platform, 'last_seen': timezone.now()}
        )
        serializer.instance = obj