from django.urls import re_path

from .consumers import InterviewRoomConsumer

websocket_urlpatterns = [
    re_path(
        r"ws/interview/(?P<room_id>[-\w]+)/$",
        InterviewRoomConsumer.as_asgi(),
    ),
]