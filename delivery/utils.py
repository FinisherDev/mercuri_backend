from math import radians, cos, sin, asin, sqrt
from datetime import timedelta, datetime
from decimal import Decimal

from django.utils import timezone
from asgiref.sync import async_to_sync # type: ignore
from channels.layers import get_channel_layer
from .models import Rider, Order, Offer, OfferEvent

def haversine(lat1: float, lon1: float, lat2: float, lon2: float):
    """
        Haversine dunction for distance calculations
    """           
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return 6371 * c

def is_within_radius(pickup_lat: float, pickup_lon: float, target_lat: float, target_lon: float, radius_km: int=3):
    """
        Checks if the pickup location is within a radius from user's lat/lon
    """
    distance = haversine(pickup_lat, pickup_lon, target_lat, target_lon)
    return distance <= radius_km

def find_nearby_riders(pickup_latitude: float, pickup_longitude: float, limit: int=5):
    declined_offers = OfferEvent.objects.filter(event='declined').values_list("offer_id", flat=True)
    excluded_riders = Offer.objects.filter(id__in=declined_offers).values_list("rider_id", flat=True)
    available_riders = Rider.objects.filter(is_available=True, latitude__isnull=False, longitude__isnull=False).exclude(id__in=excluded_riders)
    nearby_riders = [rider for rider in available_riders if is_within_radius(pickup_latitude, pickup_longitude, rider.latitude, rider.longitude)]
    nearby_riders.sort(key=lambda x: x.idle_since or datetime.min)
    return nearby_riders[:limit]

# This function is meant to calculate the effective fare based on supply and demand metrics in real-time.
# However initial testing and lack of an existing framework to hold such led to remaining unused for the meantime.
# Will be revisited with time.
def calculate_simple_supply_demand_multiplier(pickup_lat: float, pickup_lon: float, radius_km: int=3):
    now = timezone.now()
    riders = Rider.objects.filter(is_available=True, latitude__isnull=False, longitude__isnull=False)
    rider_count = 0
    for r in riders:
        if haversine(pickup_lat, pickup_lon, r.latitude, r.longitude) <= radius_km:
            rider_count += 1

    recent_orders = Order.objects.filter(created_at__gte=now - timedelta(minutes=5), status='pending')
    order_count = 0
    for o in recent_orders:
        if haversine(pickup_lat, pickup_lon, o.pickup_latitude, o.pickup_longitude) <= radius_km:
            order_count += 1

    supply = max(rider_count, 1)
    ratio = order_count / supply if supply > 0 else order_count

    if ratio <= 0.8:
        return 1.0
    elif ratio <= 1.2:
        return 1.05
    elif ratio <= 1.6:
        return 1.10
    else:
        return 1.20
    
def create_offers_for_order(order: Order) -> 'list[Offer]':
    #multiplier = calculate_simple_supply_demand_multiplier(order.pickup_latitude, order.pickup_longitude)
    suggested = Decimal(order.suggested_cost)

    effective_fare =  (suggested).quantize(Decimal("0.01")) #(suggested * Decimal(multiplier)).quantize(Decimal("0.01"))

    riders = find_nearby_riders(order.pickup_latitude, order.pickup_longitude)

    offers = []
    now = timezone.now()
    expires_at = now + timedelta(seconds=50)
    for rider in riders:
        offer = Offer.objects.create(order=order, rider=rider, fare=effective_fare, is_counter=False, expires_at=expires_at)
        OfferEvent.objects.create(offer=offer, event='sent', payload={"sent_to": str(rider.id)})
        offers.append(offer)

        layer = get_channel_layer()
        payload = {
            "type": "new_offer",
            "offer": {
                "id": str(offer.id),
                "customer": {
                    "id": str(order.customer_id),
                    "email": order.customer.email,
                    "first_name": order.customer.first_name,
                    "last_name": order.customer.last_name,
                    "phone": order.customer.phone_number,
                },
                "rider": {
                    "id": str(offer.rider_id),
                    "email": offer.rider.user.email,
                    "first_name": offer.rider.user.first_name,
                    "last_name": offer.rider.user.last_name,
                    "phone": offer.rider.user.phone_number,
                },
                #"order_id": str(order.id),
                "fare": str(offer.fare),
                #"pickup_lat": order.pickup_latitude,
                #"pickup_lon": order.pickup_longitude,
                #"dropoff_lat": order.dropoff_latitude,
                #"dropoff_lon": order.dropoff_longitude,
                "package_category": offer.order.item_category,
                "package_type": offer.order.item_type,
                "created_at": offer.created_at.isoformat(),
                "expires_at": offer.expires_at.isoformat()
            },
        }
        async_to_sync(layer.group_send)(f"user_{rider.user.id}", payload)
        print(f"Offer_{offer.id}")
        print(f"user_{rider.user.id}")
    return offers