from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer
from .services import NotificationService
from .permissions import CanSendNotification, CanViewNotification, CanManageNotificationPreferences

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, CanViewNotification]

    def get_queryset(self):
        user = self.request.user
        # Staff/admin can view all, patients only their own
        if getattr(user, 'role', None) in ['staff', 'admin', 'superadmin']:
            return Notification.objects.all()
        return Notification.objects.filter(user=user)

class NotificationDetailView(generics.RetrieveAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, CanViewNotification]
    queryset = Notification.objects.all()

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanSendNotification])
def send_notification(request):
    """Create and send a notification"""
    user_id = request.data.get('user_id')
    notification_type = request.data.get('type')
    title = request.data.get('title')
    message = request.data.get('message')
    channel = request.data.get('channel', 'sms')
    scheduled_for = request.data.get('scheduled_for')
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    service = NotificationService()
    notification = service.create_and_send_notification(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        channel=channel,
        scheduled_for=scheduled_for
    )
    return Response(NotificationSerializer(notification).data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanViewNotification])
def mark_notification_read(request, pk):
    """Mark a notification as read"""
    notification = Notification.objects.filter(id=pk, user=request.user).first()
    if not notification:
        return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
    from django.utils import timezone
    notification.read_at = timezone.now()
    notification.save()
    return Response({'message': 'Notification marked as read'})

class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated, CanManageNotificationPreferences]

    def get_object(self):
        return NotificationPreference.objects.get(user=self.request.user)
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Notification, NotificationPreference, NotificationTemplate
from .serializers import NotificationSerializer, NotificationPreferenceSerializer
from .services import NotificationService
import json

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        
        # Filter by type
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(type=notification_type)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter unread
        unread_only = self.request.query_params.get('unread')
        if unread_only == 'true':
            queryset = queryset.filter(read_at__isnull=True)
        
        return queryset.order_by('-created_at')

class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationPreferenceSerializer
    
    def get_object(self):
        preference, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preference

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
        notification.read_at = timezone.now()
        notification.save()
        
        return Response({'message': 'Notification marked as read'})
    except Notification.DoesNotExist:
        return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_read(request):
    count = Notification.objects.filter(
        user=request.user,
        read_at__isnull=True
    ).update(read_at=timezone.now())
    
    return Response({'message': f'{count} notifications marked as read'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_count(request):
    count = Notification.objects.filter(
        user=request.user,
        read_at__isnull=True
    ).count()
    
    return Response({'unread_count': count})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_test_notification(request):
    """Send a test notification to the user"""
    service = NotificationService()
    
    channel = request.data.get('channel', 'sms')
    
    notification = service.create_and_send_notification(
        user=request.user,
        notification_type='queue_update',
        title='Test Notification',
        message='This is a test notification from the hospital queue system.',
        channel=channel
    )
    
    return Response({
        'message': 'Test notification sent',
        'notification_id': notification.id
    })

@csrf_exempt
@require_POST
def twilio_webhook(request):
    """Handle Twilio delivery status webhooks"""
    try:
        # Parse Twilio webhook data
        message_sid = request.POST.get('MessageSid')
        message_status = request.POST.get('MessageStatus')
        
        if message_sid and message_status:
            # Find notification by external_id (Twilio SID)
            try:
                notification = Notification.objects.get(external_id=message_sid)
                
                if message_status == 'delivered':
                    notification.delivered_at = timezone.now()
                    notification.save()
                    
                    # Log delivery
                    service = NotificationService()
                    service.log_notification_action(
                        notification, 
                        'delivered', 
                        f"Twilio status: {message_status}"
                    )
                elif message_status in ['failed', 'undelivered']:
                    notification.mark_as_failed(f"Twilio status: {message_status}")
                    
                    # Log failure
                    service = NotificationService()
                    service.log_notification_action(
                        notification, 
                        'delivery_failed', 
                        f"Twilio status: {message_status}"
                    )
                
            except Notification.DoesNotExist:
                pass  # Notification not found, ignore
        
        return HttpResponse(status=200)
    except Exception as e:
        return HttpResponse(status=500)

@api_view(['POST'])
def process_scheduled_notifications(request):
    """Admin endpoint to process scheduled notifications"""
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    service = NotificationService()
    service.process_scheduled_notifications()
    service.process_retry_notifications()
    
    return Response({'message': 'Scheduled notifications processed'})
