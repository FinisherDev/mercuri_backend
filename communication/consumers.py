from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
from django.db.models import Q
from .models import ChatRoom
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model

User = get_user_model()

class CallConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Get JWT token from query string
        token = self.scope['query_string'].decode().split('token=')[1] if b'token=' in self.scope['query_string'] else None
        print(token)
        
        #if not token:
            #await self.close()
            #return
        
        try:
            # Verify JWT token
            UntypedToken(token)
            self.user = await self.get_user_from_token(token)
            
            if self.user == AnonymousUser or self.user == None:
                print("Cloosing now")
                await self.close()
                return
            
            # Add to user's personal group
            self.room_group_name = f"call_{self.user.id}"
            print(f"call_{self.user.id}")
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
        except (InvalidToken, TokenError):
            await self.close()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def call_notification(self, event):
        """Send call notification to user"""
        await self.send_json({
            'type': 'call_notification',
            'action': event['action'],
            'call_id': event.get('call_id'),
            'caller': event.get('caller'),
            'channel_name': event.get('channel_name'),
        })
    
    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            return User.objects.get(id=user_id)
        except:
            return AnonymousUser

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Authenticate via JWT
        token = self.scope['query_string'].decode().split('token=')[1] if b'token=' in self.scope['query_string'] else None
        
        if not token:
            await self.close()
            return
        
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            self.user = await self.get_user(user_id)
            
            if not self.user:
                await self.close()
                return
            
            # Join user's personal room (for call notifications)
            self.user_room = f"user_{self.user.id}"
            await self.channel_layer.group_add(
                self.user_room,
                self.channel_name
            )
            
            # Join all chat rooms user is part of
            rooms = await self.get_user_rooms(self.user)
            self.chat_rooms = []
            
            for room in rooms:
                room_group = f"chat_{room.id}"
                self.chat_rooms.append(room_group)
                await self.channel_layer.group_add(
                    room_group,
                    self.channel_name
                )
            
            await self.accept()
            
        except Exception as e:
            print(f"WebSocket auth error: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'user_room'):
            await self.channel_layer.group_discard(
                self.user_room,
                self.channel_name
            )
        
        if hasattr(self, 'chat_rooms'):
            for room_group in self.chat_rooms:
                await self.channel_layer.group_discard(
                    room_group,
                    self.channel_name
                )
    
    async def receive_json(self, content):
        message_type = content.get('type')
        
        if message_type == 'typing':
            room_id = content.get('room_id')
            await self.channel_layer.group_send(
                f"chat_{room_id}",
                {
                    'type': 'user_typing',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'is_typing': content.get('is_typing', True),
                }
            )
    
    # Handle incoming messages from channel layer
    async def chat_message(self, event):
        await self.send_json({
            'type': 'chat_message',
            'message': event['message']
        })
    
    async def message_deleted(self, event):
        await self.send_json({
            'type': 'message_deleted',
            'message_id': event['message_id']
        })
    
    async def message_read(self, event):
        await self.send_json({
            'type': 'message_read',
            'message_id': event['message_id'],
            'room_id': event['room_id']
        })
    
    async def user_typing(self, event):
        if event['user_id'] != self.user.id:
            await self.send_json({
                'type': 'user_typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            })
    
    async def call_notification(self, event):
        await self.send_json({
            'type': 'call_notification',
            'action': event['action'],
            'call_id': event.get('call_id'),
            'caller': event.get('caller'),
            'channel_name': event.get('channel_name'),
        })
    
    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_user_rooms(self, user):
        return list(ChatRoom.objects.filter(
            Q(participant_1=user) | Q(participant_2=user)
        ))
