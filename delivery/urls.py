import delivery.views as delivery_views
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'orders', delivery_views.OrderViewSet, 'orders')

urlpatterns = [
    path('', include(router.urls)),
    path('offers/<uuid:offer_id>/driver_accept/', delivery_views.driver_accept),
    path('offers/<uuid:offer_id>/customer_accept/', delivery_views.customer_accept),
    path('offers/<uuid:offer_id>/counter/', delivery_views.counter_offer),
    path('offers/<uuid:offer_id>/decline/', delivery_views.decline_offer),
]