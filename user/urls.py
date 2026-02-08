from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from user import views

app_name = 'user'

urlpatterns = [
     path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
     path('register/', views.CustomUserRegisterationAPIView.as_view(),
         name="create-user"),
     path('login/', views.CustomUserLoginAPIView.as_view(), name="login-user"),
     path('logout/', views.CustomUserLogoutAPIView.as_view(), name='logout-user'),
     path('', views.CustomUserAPIView.as_view(), name='user-info'),
     path('customer-profile/', views.CustomerProfileAPIView.as_view(),
          name='customer-profile'),
     path('rider-profile/', views.RiderProfileAPIView.as_view(),
          name='rider-profile'),
     #path('profile/avatar/', views.UserAvatarAPIView.as_view(),
          #name='user-avatar'),
     path('password/change/', views.PasswordChangeAPIView.as_view(),
          name='change-password'),
]
