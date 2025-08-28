from django.urls import re_path
from . import consumers

# WebSocket routing for notifications
websocket_urlpatterns = [
    # Notification channel for real-time updates
    re_path(r'^ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    # Add more consumers here as needed
]
