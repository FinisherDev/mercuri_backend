from datetime import timedelta

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import Order, Rider, Offer, OfferEvent
from .serializers import OrderCreateSerializer, OrderSerializer, OfferSerializer
from .tasks import dispatch_offers
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Create your views here.

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = (permissions.IsAuthenticated, )

    def get_serializer_class(self):
        if self.action in ['create']:
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        now = timezone.now()
        expires = now + timedelta(seconds=60)
        order = serializer.save(customer = self.request.user, expires_at=expires)
        dispatch_offers.delay(str(order.id))


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def driver_accept(request, offer_id):
    """
        Driver accepts an order
    """
    offer = get_object_or_404(Offer, pk=offer_id)
    rider = Rider.objects.get(user=request.user)

    now = timezone.now()
    if offer.expires_at and now > offer.expires_at:
        OfferEvent.objects.create(offer=offer, event='expired', payload={})
        return Response({"detail": "Offer expired"}, status=400)
    
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=offer.order_id)

        if order.status == "accepted" or order.rider is not None:
            return Response({"detail": "Order has already been accepted by a rider"}, status=409)
        if order.status != "pending":
            return Response({"error": "Not available"}, status=400)
        
        order.rider = rider
        order.status = 'accpeted'
        order.accepted_at = timezone.now()
        order.save()

        offer.accepted = True
        offer.save()
        OfferEvent.objects.create(offer=offer, event='accepted', payload={"rider_accepted": str(rider.id)})

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f'user_{order.customer.id}', {
        "type": "offer_accepted",
        "offer": {
            "id": str(offer.id),
            "rider": {
                    "id": str(order.rider.user.id),
                    "email": order.rider.user.email,
                    "first_name": order.rider.user.first_name,
                    "last_name": order.rider.user.last_name,
                    "phone": order.rider.user.phone_number,
            },
        },
    })

    return Response({"status" : "Order accepted", "order_id": str(order.id)})

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def customer_accept(request, offer_id):
    """
        Driver accepts an order
    """
    offer = get_object_or_404(Offer, pk=offer_id)
    rider = offer.rider

    now = timezone.now()
    if offer.expires_at and now > offer.expires_at:
        OfferEvent.objects.create(offer=offer, event='expired', payload={})
        return Response({"detail": "Offer expired"}, status=400)
    
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=offer.order_id)

        if order.status == "accepted" or order.rider is not None:
            return Response({"detail": "Order has already been accepted by a rider"}, status=409)
        if order.status != "pending":
            return Response({"error": "Not available"}, status=400)
        
        order.rider = rider
        order.status = 'accpeted'
        order.accepted_at = timezone.now()
        order.save()

        offer.accepted = True
        offer.save()
        OfferEvent.objects.create(offer=offer, event='accepted', payload={"rider_accepted": str(rider.id)})

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f'user_{order.customer.id}', {
        "type": "offer_accepted",
        "offer": {
            "id": str(offer.id),
            "rider": {
                    "id": str(order.rider.id),
                    "email": order.rider.user.email,
                    "first_name": order.rider.user.first_name,
                    "last_name": order.rider.user.last_name,
                    "phone": order.rider.user.phone_number,
            },
        },
    })

    return Response({"status" : "Order accepted", "order_id": str(order.id)})

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def counter_offer(request, offer_id):
    offer = get_object_or_404(Offer, pk=offer_id)
    user = request.user
    
    fare = request.data.get("counter_fee")
    if fare is None:
        return Response({"detail": "Fare required"}, status=400)
    
    now = timezone.now()
    expires_at = now + timedelta(seconds=30)
    Offer.objects.filter(id=offer_id).update(fare=fare, is_counter=True, expires_at=expires_at)
    OfferEvent.objects.create(offer=offer, event='countered', payload={"fare": str(fare)})

    if user.role == "rider":
        async_to_sync(get_channel_layer().group_send)(f"user_{str(offer.order.customer.id)}", {
            "type": "offer_countered",
            "offer": {
                "id": str(offer.id),
                "price": offer.fare,
            }
        })
    else:
        async_to_sync(get_channel_layer().group_send)(f"user_{str(offer.rider.user.id)}", {
            "type": "offer_countered",
            "offer": {
                "id": str(offer.id),
                "price": offer.fare,
            }
        })

    return Response(OfferSerializer(offer).data, status=201)

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def decline_offer(request, offer_id):
    rider = Rider.objects.get(user=request.user)
    offer = get_object_or_404(Offer, id=offer_id, rider=rider)

    now = timezone.now()
    if offer.expires_at and now > offer.expires_at:
        OfferEvent.objects.create(offer=offer, event='expired', payload={})
        return Response({"detail": "Offer expired"}, status=400)
    
    OfferEvent.objects.create(offer=offer, event='declined')
    return Response({"detail": "Declined"}, status=200)
        