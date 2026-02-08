from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from agora_token_builder import RtcTokenBuilder
from django.conf import settings
from django.db import models
import time
import uuid
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Call
from .serializers import CallSerializer
from user.serializers import CustomUserSerializer
from .models import ChatRoom, Message, ChatRoomMembership, FCMDevice
from .serializers import (ChatRoomSerializer, MessageSerializer, 
                          FCMDeviceSerializer)
from .notifications import send_fcm_notification

User = get_user_model()

class CallViewSet(viewsets.ModelViewSet):
    serializer_class = CallSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Call.objects.filter(
            models.Q(caller=user) | models.Q(receiver=user)
        )
    
    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """Initiate a call to another user"""
        receiver_id = request.data.get('receiver_id')
        print("Here", receiver_id)
        
        if not receiver_id:
            return Response(
                {'error': 'receiver_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if str(receiver_id) == str(request.user.id):
            return Response(
                {'error': 'Cannot call yourself'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        receiver = get_object_or_404(User, id=receiver_id)
        
        # Check if there's already an active call
        active_call = Call.objects.filter(
            models.Q(caller=request.user, status__in=['initiated', 'ringing', 'accepted']) |
            models.Q(receiver=request.user, status__in=['initiated', 'ringing', 'accepted'])
        ).first()
        
        if active_call:
            print("Active")
            return Response(
                {'error': 'You already have an active call'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create unique channel name
        channel_name = f"call_{uuid.uuid4().hex[:12]}"
        
        # Create call record
        call = Call.objects.create(
            caller=request.user,
            receiver=receiver,
            channel_name=channel_name,
            status='initiated'
        )

        print(f"Call_{receiver.id}")
        print("User Data:", CustomUserSerializer(request.user).data)
        
        # Send notification to receiver via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"call_{receiver.id}",
            {
                'type': 'call_notification',
                'action': 'incoming_call',
                'call_id': call.id,
                'caller': CustomUserSerializer(request.user).data,
                'channel_name': channel_name,
            }
        )
        
        call.status = 'ringing'
        call.save()
        
        return Response(CallSerializer(call).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept an incoming call"""
        call = self.get_object()
        
        if call.receiver != request.user:
            return Response(
                {'error': 'You are not the receiver of this call'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if call.status not in ['initiated', 'ringing']:
            return Response(
                {'error': 'Call cannot be accepted'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        call.status = 'accepted'
        call.started_at = timezone.now()
        call.save()
        
        # Notify caller that call was accepted
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"call_{call.caller.id}",
            {
                'type': 'call_notification',
                'action': 'call_accepted',
                'call_id': call.id,
                'channel_name': call.channel_name,
            }
        )
        
        return Response(CallSerializer(call).data)
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline an incoming call"""
        call = self.get_object()
        
        if call.receiver != request.user:
            return Response(
                {'error': 'You are not the receiver of this call'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if call.status not in ['initiated', 'ringing']:
            return Response(
                {'error': 'Call cannot be declined'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        call.status = 'declined'
        call.ended_at = timezone.now()
        call.save()
        
        # Notify caller that call was declined
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"call_{call.caller.id}",
            {
                'type': 'call_notification',
                'action': 'call_declined',
                'call_id': call.id,
            }
        )
        
        return Response(CallSerializer(call).data)
    
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End an active call"""
        call = self.get_object()
        
        if call.caller != request.user and call.receiver != request.user:
            return Response(
                {'error': 'You are not part of this call'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if call.status == 'accepted' and call.started_at:
            call.duration = int((timezone.now() - call.started_at).total_seconds())
        
        call.status = 'ended'
        call.ended_at = timezone.now()
        call.save()
        
        # Notify the other user that call ended
        other_user_id = call.receiver.id if call.caller == request.user else call.caller.id
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"call_{other_user_id}",
            {
                'type': 'call_notification',
                'action': 'call_ended',
                'call_id': call.id,
            }
        )
        
        return Response(CallSerializer(call).data)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get call history for the authenticated user"""
        calls = self.get_queryset().filter(
            status__in=['ended', 'declined', 'missed']
        )[:50]
        
        serializer = self.get_serializer(calls, many=True)
        return Response(serializer.data)


"""@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_agora_token(request):
    ""Generate Agora RTC token for authenticated user""
    call_id = request.data.get('call_id')
    
    if not call_id:
        return Response(
            {'error': 'call_id is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        call = Call.objects.get(id=call_id)
        
        # Verify user is part of the call
        if request.user not in [call.caller, call.receiver]:
            return Response(
                {'error': 'You are not part of this call'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        channel_name = call.channel_name
        uid = request.user.id
        
        # Token expiration time (1 hour)
        expiration_time = int(time.time()) + 3600
        
        # Generate token
        token = RtcTokenBuilder.buildTokenWithUid(
            settings.AGORA_APP_ID,
            settings.AGORA_APP_CERTIFICATE,
            channel_name,
            uid,
            1,  # Publisher role
            expiration_time
        )
        response = Response({
            'token': token,
            'appId': settings.AGORA_APP_ID,
            'channelName': channel_name,
            'uid': uid,
            'expiration': expiration_time
        })
        print(response)
        
        return Response({
            'token': token,
            'appId': settings.AGORA_APP_ID,
            'channelName': channel_name,
            'uid': uid,
            'expiration': expiration_time
        })
        
    except Call.DoesNotExist:
        return Response(
            {'error': 'Call not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )"""
    

class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatRoom.objects.filter(
            models.Q(participant_1=self.request.user) | models.Q(participant_2=self.request.user)
        ).annotate(
            last_message_time=Max('messages__created_at')
        ).order_by('-last_message_time')
    
    @action(detail=False, methods=['post'])
    def create_or_get(self, request):
        """Create or get existing chat room with another user"""
        other_user_id = request.data.get('user_id')
        
        if not other_user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if str(other_user_id) == str(request.user.id):
            return Response(
                {'error': 'Cannot create chat with yourself'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        other_user = get_object_or_404(User, id=other_user_id)
        
        # Check if chat already exists (in either direction)
        existing_room = ChatRoom.objects.filter(
            models.Q(participant_1=request.user, participant_2=other_user) |
            models.Q(participant_1=other_user, participant_2=request.user)
        ).first()
        
        if existing_room:
            serializer = self.get_serializer(existing_room)
            return Response(serializer.data)
        
        # Create new chat room
        room = ChatRoom.objects.create(
            participant_1=request.user,
            participant_2=other_user
        )
        
        # Create memberships
        ChatRoomMembership.objects.create(room=room, user=request.user)
        ChatRoomMembership.objects.create(room=room, user=other_user)
        
        serializer = self.get_serializer(room)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark all messages in room as read"""
        room = self.get_object()
        
        # Verify user is participant
        if request.user not in [room.participant_1, room.participant_2]:
            return Response(
                {'error': 'You are not a participant in this chat'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        membership, created = ChatRoomMembership.objects.get_or_create(
            room=room,
            user=request.user
        )
        membership.last_read_at = timezone.now()
        membership.save()
        
        # Mark all unread messages as read
        now = timezone.now()
        unread_messages = room.messages.filter(
            is_read=False
        ).exclude(sender=request.user)
        
        for message in unread_messages:
            message.is_read = True
            message.read_at = now
            message.save()
            
            # Notify sender about read receipt
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{message.sender.id}",
                {
                    'type': 'message_read',
                    'message_id': message.id,
                    'room_id': room.id,
                }
            )
        
        return Response({'status': 'marked as read'})
    
    @action(detail=True, methods=['post'])
    def toggle_mute(self, request, pk=None):
        """Mute or unmute a chat"""
        room = self.get_object()
        
        membership, created = ChatRoomMembership.objects.get_or_create(
            room=room,
            user=request.user
        )
        
        membership.is_muted = not membership.is_muted
        membership.save()
        
        return Response({
            'is_muted': membership.is_muted
        })


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        room_id = self.request.query_params.get('room_id')
        if room_id:
            # Verify user is participant
            room = ChatRoom.objects.filter(
                id=room_id
            ).filter(
                models.Q(participant_1=self.request.user) | models.Q(participant_2=self.request.user)
            ).first()
            
            if room:
                return Message.objects.filter(
                    room_id=room_id,
                    is_deleted=False
                )
        return Message.objects.none()
    
    def create(self, request, *args, **kwargs):
        room_id = request.data.get('room')
        
        if not room_id:
            return Response(
                {'error': 'room is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        room = get_object_or_404(ChatRoom, id=room_id)
        
        # Verify user is participant
        if request.user not in [room.participant_1, room.participant_2]:
            return Response(
                {'error': 'You are not a participant in this chat'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(sender=request.user, room=room)
        
        # Update room timestamp
        room.updated_at = timezone.now()
        room.save()
        
        # Send real-time notification via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{room.id}",
            {
                'type': 'chat_message',
                'message': MessageSerializer(message).data
            }
        )
        
        # Send FCM notification to other participant
        other_participant = room.get_other_participant(request.user)
        
        # Check if user has muted this chat
        membership = ChatRoomMembership.objects.filter(
            room=room, user=other_participant
        ).first()
        
        if membership and not membership.is_muted:
            send_fcm_notification(
                user=other_participant,
                title=f"{request.user.username}",
                body=message.content[:100],
                data={
                    'type': 'chat_message',
                    'room_id': str(room.id),
                    'message_id': str(message.id),
                }
            )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def soft_delete(self, request, pk=None):
        """Soft delete a message"""
        message = self.get_object()
        
        if message.sender != request.user:
            return Response(
                {'error': 'You can only delete your own messages'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.is_deleted = True
        message.content = "This message was deleted"
        message.save()
        
        # Notify via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{message.room.id}",
            {
                'type': 'message_deleted',
                'message_id': message.id,
            }
        )
        
        return Response({'status': 'message deleted'})


class FCMDeviceViewSet(viewsets.ModelViewSet):
    serializer_class = FCMDeviceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return FCMDevice.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Deactivate old tokens for this device type
        FCMDevice.objects.filter(
            user=self.request.user,
            device_type=self.request.data.get('device_type')
        ).update(is_active=False)
        
        serializer.save(user=self.request.user, is_active=True)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users(request):
    """Search for users to start a chat with"""
    query = request.query_params.get('q', '')
    
    if len(query) < 2:
        return Response(
            {'error': 'Query must be at least 2 characters'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    users = User.objects.filter(
        models.Q(username__icontains=query) |
        models.Q(first_name__icontains=query) |
        models.Q(last_name__icontains=query)
    ).exclude(id=request.user.id)[:20]
    
    serializer = CustomUserSerializer(users, many=True)
    return Response(serializer.data)
