import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Rider

class DeliveryConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        print("USer is", self.user)
        
        if self.user == AnonymousUser:
            print(f"User {self.user.id} disconnected")
            await self.close()
            return
        
        else:
            self.group_name = f'user_{self.user.id}'
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            print(f"User {self.user.id} connected suuccessfully")

    async def disconnect(self, close_code):
        user = self.scope["user"]
        if self.user == AnonymousUser:
            if hasattr(self, 'group_name'):
                await self.channel_layer.group_discard(
                    self.group_name,
                    self.channel_name
                )
                print(f"User {str(user.id)} disconnected")

    async def new_offer(self, event):
        print("Preparing to send new offer")
        await self.send(text_data=json.dumps({
            "type": "new_offer",
            "offer": event["offer"]
        }))
        print("Offer sent")

    async def offer_expired(self, event):
        await self.send(text_data=json.dumps({
            "type": "offer_expired",
            "offer_id": event["offer_id"]
        }))

    async def offer_accepted(self, event):
        await self.send(text_data=json.dumps({
            "type": "offer_accepted",
            "offer": event["offer"]
        }))

    async def offer_countered(self, event):
        await self.send(text_data=json.dumps({
            "type": "offer_countered",
            "offer": event["offer"]
        }))

    async def offer_cancelled(self, event):
        await self.send(text_data=json.dumps({
            "type": "offer_cancelled",
            "offer_id": event["offer_id"]
        }))

class RiderLocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        print("User is", self.user)
        
        if self.user == AnonymousUser:
            print(f"User {self.user.id} disconnected")
            await self.close()
            return
        
        else:
            self.group_name = f'user_{self.user.id}'
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            print(f"User {self.user.id} connected suuccessfully")

    async def disconnect(self, close_code):
        user = self.scope["user"]
        if self.user == AnonymousUser:
            if hasattr(self, 'group_name'):
                await self.channel_layer.group_discard(
                    self.group_name,
                    self.channel_name
                )
                print(f"User {str(user.id)} disconnected")

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data['type'] == 'update_location':
            await self.update_driver_location(
                longitude = data['longitude'],
                latitude = data['latitude'],
                heading= data.get('heading'),
                speed = data.get('speed'),
                accuracy = data.get('accuracy')
            )

    async def location_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'latitude': event['latitude'],
            'longitude': event['longitude'],
            'heading': event.get('heading'),
            'speed': event.get('speed')
        }))

    @database_sync_to_async
    def update_driver_location(self, longitude, latitude, heading, speed, accuracy):
        user = self.scope["user"]
        Rider.objects.filter(user=user).update(
            latitude=latitude, 
            longitude=longitude, 
            heading=heading,
            speed=speed,
            accuracy=accuracy
        )

        