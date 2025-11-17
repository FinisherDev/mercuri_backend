from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

from .models import CustomUser

ROLE_CHOICES = [
    ('customer', 'Customer'),
    ('driver', 'Driver'),
]

class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer class to seralize CustomUser model.
    """
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'first_name', 'phone_number')

class CustomUserRegisterationSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize registeration requests and create a new user.
    """
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'phone_number', 'password', 'role')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class CustomUserLoginSerializer(serializers.Serializer):
    """
    Serializer class to authenticate users with email and password.
    """
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=ROLE_CHOICES)

    def validate(self, data):
        user = authenticate(**data)
        if data['role'] == user.role:
            if user and user.is_active:
                return user
            raise serializers.ValidationError('Incorrect Credentials')
        raise serializers.ValidationError('Role mismatch')


#class ProfileSerializer(CustomUserSerializer):
    """
    Serializer class to serialize the user Profile model
    """
#    class Meta:
#        model = Profile
 #       fields = ('bio')


#class ProfileAvatarSerializer(serializers.ModelSerializer):
    """
    Serializer class to serialize the avatar
    """
#    class Meta:
#        model = Profile
#        fields = ('avatar',)


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer class for changing user password
    """
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance
