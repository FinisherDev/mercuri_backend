from rest_framework import serializers
from user.serializers import CustomUserSerializer
from .models import Call, ChatRoom, FCMDevice, Message

class CallSerializer(serializers.ModelSerializer):
    caller = CustomUserSerializer(read_only=True)
    receiver = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = Call
        fields = ['id', 'caller', 'receiver', 'channel_name', 'status', 
                  'created_at', 'started_at', 'ended_at', 'duration']
        read_only_fields = ['channel_name', 'created_at', 'started_at', 'ended_at', 'duration']

class MessageSerializer(serializers.ModelSerializer):
    sender = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'room', 'sender', 'message_type', 'content', 
                  'file_url', 'created_at', 'edited_at', 'is_deleted', 
                  'is_read', 'read_at']
        read_only_fields = ['sender', 'created_at', 'is_read', 'read_at']


class ChatRoomSerializer(serializers.ModelSerializer):
    other_participant = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'other_participant', 'created_at', 'updated_at', 
                  'last_message', 'unread_count']
    
    def get_other_participant(self, obj):
        request = self.context.get('request')
        if request and request.user:
            other = obj.get_other_participant(request.user)
            if other:
                return CustomUserSerializer(other).data
        return None
    
    def get_last_message(self, obj):
        last_msg = obj.messages.filter(is_deleted=False).last()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.get_unread_count(request.user)
        return 0


class FCMDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMDevice
        fields = ['id', 'registration_token', 'device_type', 'is_active']
        read_only_fields = ['user']
