import json
from datetime import timedelta
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import InterviewRoom, InterviewRoomParticipant


class InterviewRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"interview_{self.room_id}"
        self.session_id = self.get_session_id()
        self.joined_room = False

        admitted = await self.reserve_room_slot()

        if not admitted:
            await self.accept()
            await self.send(text_data=json.dumps({
                "type": "room_full",
                "payload": {
                    "message": "This interview room already has two users.",
                },
            }))
            await self.close(code=4001)
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        self.joined_room = True

        await self.accept()
        await self.broadcast_presence()

    async def disconnect(self, close_code):
        if not getattr(self, "joined_room", False):
            return

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

        await self.release_room_slot()
        await self.broadcast_presence()

    async def receive(self, text_data):
        await self.touch_room_slot()

        data = json.loads(text_data)
        event_type = data.get("type")

        if event_type == "heartbeat":
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "broadcast_editor_event",
                "event_type": event_type,
                "payload": data.get("payload", {}),
                "sender_channel_name": self.channel_name,
            },
        )

    async def broadcast_editor_event(self, event):
        event_type = event["event_type"]

        if (
            event_type
            and event_type.startswith("webrtc_")
            and event.get("sender_channel_name") == self.channel_name
        ):
            return

        await self.send(text_data=json.dumps({
            "type": event_type,
            "payload": event["payload"],
        }))

    async def broadcast_presence(self):
        users_count = await self.get_room_users_count()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "presence_update",
                "users_count": users_count,
            },
        )

    async def presence_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "presence_update",
            "payload": {
                "users_count": event["users_count"],
            },
        }))

    @database_sync_to_async
    def reserve_room_slot(self):
        max_users = getattr(settings, "INTERVIEW_ROOM_MAX_USERS", 2)

        with transaction.atomic():
            self.delete_stale_participants()
            room, _ = InterviewRoom.objects.get_or_create(room_id=self.room_id)
            room = InterviewRoom.objects.select_for_update().get(room_id=room.room_id)

            InterviewRoomParticipant.objects.filter(
                channel_name=self.channel_name,
            ).delete()
            InterviewRoomParticipant.objects.filter(
                room=room,
                session_id=self.session_id,
            ).delete()

            if room.participants.count() >= max_users:
                return False

            InterviewRoomParticipant.objects.create(
                room=room,
                channel_name=self.channel_name,
                session_id=self.session_id,
            )
            return True

    @database_sync_to_async
    def release_room_slot(self):
        with transaction.atomic():
            InterviewRoomParticipant.objects.filter(
                channel_name=self.channel_name,
            ).delete()

            if not InterviewRoomParticipant.objects.filter(room_id=self.room_id).exists():
                InterviewRoom.objects.filter(room_id=self.room_id).delete()

    @database_sync_to_async
    def touch_room_slot(self):
        InterviewRoomParticipant.objects.filter(
            channel_name=self.channel_name,
        ).update(last_seen=timezone.now())

    @database_sync_to_async
    def get_room_users_count(self):
        self.delete_stale_participants()
        return InterviewRoomParticipant.objects.filter(room_id=self.room_id).count()

    @staticmethod
    def delete_stale_participants():
        ttl_seconds = getattr(settings, "INTERVIEW_ROOM_PRESENCE_TTL_SECONDS", 90)
        stale_before = timezone.now() - timedelta(seconds=ttl_seconds)

        InterviewRoomParticipant.objects.filter(
            last_seen__lt=stale_before,
        ).delete()

        InterviewRoom.objects.filter(participants__isnull=True).delete()

    def get_session_id(self):
        query_params = parse_qs(self.scope.get("query_string", b"").decode())
        session_id = query_params.get("clientId", [self.channel_name])[0]

        return session_id[:128] or self.channel_name
