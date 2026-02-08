from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/delivery/$', consumers.DeliveryConsumer.as_asgi()),
    re_path(r'ws/driver-locations/$', consumers.RiderLocationConsumer.as_asgi())
]