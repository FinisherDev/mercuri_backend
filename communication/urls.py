from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'calls', views.CallViewSet, 'calls')
router.register(r'chat/rooms', views.ChatRoomViewSet, basename='chatroom')
router.register(r'chat/messages', views.MessageViewSet, basename='message')
router.register(r'fcm/devices', views.FCMDeviceViewSet, basename='fcmdevice')

urlpatterns = [
    path('comms/', include(router.urls)),
    #path('agora/token/', views.generate_agora_token, name='generate_agora_token'),
    path('users/search/', views.search_users, name='search_users'),
]