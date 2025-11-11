import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Call
from django.utils import timezone

User = get_user_model()

class CallConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return
        self.group_name = f"user_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        """
        Expect messages:
        - {"action":"answer","call_id":"...","accepted":true}
        - {"action":"hangup","call_id":"..."}
        """
        user = self.scope["user"]
        action = content.get("action")

        if action == "answer":
            call_id = content.get("call_id")
            accepted = bool(content.get("accepted", False))
            # update DB and notify caller
            call = await database_sync_to_async(Call.objects.get)(pk=call_id)
            if accepted:
                call.status = Call.STATUS_ONGOING
                call.accepted_at = timezone.now()
                await database_sync_to_async(call.save)()
                # notify caller
                await self.channel_layer.group_send(
                    f"user_{call.caller_id}",
                    {
                        "type": "call.response",
                        "call_id": str(call.id),
                        "accepted": True,
                        "callee_id": user.id,
                    }
                )
            else:
                call.status = Call.STATUS_REJECTED
                await database_sync_to_async(call.save)()
                await self.channel_layer.group_send(
                    f"user_{call.caller_id}",
                    {
                        "type": "call.response",
                        "call_id": str(call.id),
                        "accepted": False,
                        "callee_id": user.id,
                    }
                )

        elif action == "hangup":
            call_id = content.get("call_id")
            # update call ended
            try:
                call = await database_sync_to_async(Call.objects.get)(pk=call_id)
                call.ended_at = timezone.now()
                call.status = Call.STATUS_COMPLETED
                await database_sync_to_async(call.save)()
                # notify other party (best-effort)
                other_id = call.caller_id if user.id == call.callee_id else call.callee_id
                await self.channel_layer.group_send(
                    f"user_{other_id}",
                    {
                        "type": "call.ended",
                        "call_id": str(call.id),
                    }
                )
            except Call.DoesNotExist:
                pass

    # Handlers for group messages
    async def incoming_call(self, event):
        await self.send_json({
            "type": "incoming_call",
            "call_id": event["call_id"],
            "caller_id": event["caller_id"],
            "caller_display": event.get("caller_display"),
            "channel_name": event["channel_name"],
            "token": event["token"],
        })

    async def call_response(self, event):
        await self.send_json({
            "type": "call_response",
            "call_id": event["call_id"],
            "accepted": event["accepted"],
            "callee_id": event.get("callee_id"),
        })

    async def call_ended(self, event):
        await self.send_json({
            "type": "call_ended",
            "call_id": event["call_id"],
        })
