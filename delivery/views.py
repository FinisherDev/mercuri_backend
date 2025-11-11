from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order, Driver
from .serializers import OrderCreateSerializer, OrderSerializer
from django.utils import timezone

# Create your views here.

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = (permissions.AllowAny, )

    def get_serializer_class(self):
        if self.action in ['create']:
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(customer = self.request.user)
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
            Get orders within 3km of the driver's location.
        """
        try:
            driver = Driver.objects.get(user=request.user)
        except Driver.DoesNotExist:
            return Response({"error" : "This user is not a driver"})
        if not driver.is_available or Driver.objects.filter(user=request.user).exists() == False:
            return Response({"error" : "Only available drivers can take orders"})
        
        available_orders = Order.objects.filter(driver__isnull=True)
        nearby = [order for order in available_orders if order.is_within_radius(driver.latitude, driver.longitude)]

        serializer = self.get_serializer(nearby, many=True)
        print(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def accept(self, request, pk=None):
        """
            Driver accepts an order
        """
        order = self.get_object()
        driver = Driver.objects.get(user=request.user)

        if not driver.is_available or Driver.objects.filter(user=request.user).exists() == False:
            return Response({"error" : "Only available drivers can take orders"})
        
        if order.driver is not None:
            return Response({"error" : "Order has already been accepted by a driver"})

        order.driver = driver
        order.accepted_at = timezone.now()
        order.save()

        return Response({"status" : "Order accepted"})
