from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView, CreateAPIView, UpdateAPIView, RetrieveUpdateAPIView, RetrieveAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from . import serializers, models

# Create your views here.

User = get_user_model()


class CustomUserRegisterationAPIView(GenericAPIView):
    """
    An endpoint for the client to create a new User. 
    """
    permission_classes = (AllowAny,)
    serializer_class = serializers.CustomUserRegisterationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = RefreshToken.for_user(user)
        data = serializer.data
        data['tokens'] = {
            'refresh': str(token),
            'access': str(token.access_token)
        }
        return Response(data,status=status.HTTP_201_CREATED)


class CustomUserLoginAPIView(GenericAPIView):
    """
    An endpoint to authenticate existing users using their email and password.
    """
    permission_classes = (AllowAny,)
    serializer_class = serializers.CustomUserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        serializer = serializers.CustomUserSerializer(user)
        token = RefreshToken.for_user(user)
        data = serializer.data
        data['tokens'] = {
            'refresh': str(token),
            'access': str(token.access_token)
        }
        print(f"Access Token {token.access_token}")
        return Response(data, status=status.HTTP_200_OK)


class CustomUserLogoutAPIView(GenericAPIView):
    """
    An endpoint to logout users.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class CustomUserAPIView(RetrieveUpdateAPIView):
    """
    Get, Update user information
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.CustomUserSerializer

    def get_object(self):
        return self.request.user


class CustomerProfileAPIView(RetrieveUpdateAPIView):
    """
    Get, Update user profile
    """
    queryset = models.CustomerProfile.objects.all()
    serializer_class = serializers.CustomerProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user.profile


class RiderProfileCreateAPIView(CreateAPIView):
    """
    Get, Update user avatar
    """
    serializer_class = serializers.RiderProfileSerializer
    permission_classes = (IsAuthenticated,)
    
class RiderProfileUpdateView(UpdateAPIView):
    serializer_class = serializers.RiderProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user.rider_profile
    
class RiderProfileStatusAPIView(RetrieveAPIView):
    serializer_class = serializers.RiderProfileStatusSerializer
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        user = request.user

        if user.is_rider() != 'rider':
            return Response({
                'rider_registered': False,
                'rider_profile_created': False,
                'is_fully_registered': False,
                'can_accept_deliveries': False,
                })

        if not hasattr(user, 'rider_profile'):
            return Redsponse({
                'rider_registered': True,
                'rider_profile_created': False,
                'is_fully_registered': False,
                'can_accept_deliveries': False,
                })
        
        serializer = self.get_serializer(user.rider_profile)
        return Response(serializer.data)

class PasswordChangeAPIView(UpdateAPIView):
    """
    Change password view for authenticated user
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.PasswordChangeSerializer

    def get_object(self):
        return self.request.user
