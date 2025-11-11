from django.urls import path
from .consumers import TransactionConsumer

websocket_urlpatterns = [
    path("ws/transactions/<str:user_id>/", TransactionConsumer.as_asgi()),
]