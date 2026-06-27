import json

from channels.generic.websocket import AsyncWebsocketConsumer


class InterviewRoomConsumer(AsyncWebsocketConsumer):
    room_users = {}

    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"interview_{self.room_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        if self.room_group_name not in self.room_users:
            self.room_users[self.room_group_name] = set()

        self.room_users[self.room_group_name].add(self.channel_name)

        await self.accept()

        await self.broadcast_presence()

    async def disconnect(self, close_code):
        if self.room_group_name in self.room_users:
            self.room_users[self.room_group_name].discard(self.channel_name)

            if not self.room_users[self.room_group_name]:
                del self.room_users[self.room_group_name]

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

        await self.broadcast_presence()

    async def receive(self, text_data):
        data = json.loads(text_data)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "broadcast_editor_event",
                "event_type": data.get("type"),
                "payload": data.get("payload", {}),
            },
        )

    async def broadcast_editor_event(self, event):
        await self.send(text_data=json.dumps({
            "type": event["event_type"],
            "payload": event["payload"],
        }))

    async def broadcast_presence(self):
        users_count = len(self.room_users.get(self.room_group_name, set()))

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