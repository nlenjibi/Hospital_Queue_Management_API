import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

User = get_user_model()

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get token from query string
        query_string = self.scope['query_string'].decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        if token:
            try:
                # Validate JWT token
                UntypedToken(token)
                self.user = await self.get_user_from_token(token)
                
                if self.user and not isinstance(self.user, AnonymousUser):
                    # Join user-specific group
                    self.user_group_name = f"user_{self.user.id}"
                    
                    await self.channel_layer.group_add(
                        self.user_group_name,
                        self.channel_name
                    )
                    
                    await self.accept()
                    
                    # Send connection confirmation
                    await self.send(text_data=json.dumps({
                        'type': 'connection_established',
                        'message': 'Connected to notification service'
                    }))
                else:
                    await self.close()
            except (InvalidToken, TokenError):
                await self.close()
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        # Leave user group
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'mark_read':
                notification_id = text_data_json.get('notification_id')
                if notification_id:
                    await self.mark_notification_read(notification_id)
            elif message_type == 'get_unread_count':
                count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'unread_count',
                    'count': count
                }))
        except json.JSONDecodeError:
            pass
    
    # Receive message from room group
    async def notification_message(self, event):
        notification = event['notification']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': notification
        }))
    
    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            return User.objects.get(id=user_id)
        except:
            return None
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        try:
            from .models import Notification
            from django.utils import timezone
            
            notification = Notification.objects.get(
                id=notification_id,
                user=self.user
            )
            notification.read_at = timezone.now()
            notification.save()
            return True
        except:
            return False
    
    @database_sync_to_async
    def get_unread_count(self):
        try:
            from .models import Notification
            return Notification.objects.filter(
                user=self.user,
                read_at__isnull=True
            ).count()
        except:
            return 0
