from django.shortcuts import redirect
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, RetrieveUpdateAPIView, UpdateAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, login, logout
from django.shortcuts import get_object_or_404


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


class RiderProfileAPIView(RetrieveUpdateAPIView):
    """
    Get, Update user avatar
    """
    queryset = models.RiderProfile.objects.all()
    serializer_class = serializers.RiderProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user.profile


class PasswordChangeAPIView(UpdateAPIView):
    """
    Change password view for authenticated user
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.PasswordChangeSerializer

    def get_object(self):
        return self.request.user
