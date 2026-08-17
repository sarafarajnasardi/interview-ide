from django.db import models


class InterviewRoom(models.Model):
    room_id = models.CharField(max_length=128, primary_key=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.room_id


class InterviewRoomParticipant(models.Model):
    room = models.ForeignKey(
        InterviewRoom,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    channel_name = models.CharField(max_length=255, unique=True)
    session_id = models.CharField(max_length=128, blank=True, null=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["room", "last_seen"]),
            models.Index(fields=["room", "session_id"]),
        ]

    def __str__(self):
        return f"{self.room_id}:{self.channel_name}"
