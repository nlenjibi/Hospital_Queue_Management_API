from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from .models import Notification, NotificationPreference, NotificationTemplate, NotificationLog
import json
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        else:
            self.twilio_client = None
            logger.warning("Twilio credentials not configured")
        
        self.channel_layer = get_channel_layer()
    
    def get_user_preferences(self, user):
        """Get or create user notification preferences"""
        preferences, created = NotificationPreference.objects.get_or_create(user=user)
        return preferences
    
    def is_quiet_hours(self, user):
        """Check if current time is within user's quiet hours"""
        preferences = self.get_user_preferences(user)
        current_time = timezone.now().time()
        
        if preferences.quiet_hours_start <= preferences.quiet_hours_end:
            # Same day quiet hours (e.g., 22:00 to 08:00 next day)
            return current_time >= preferences.quiet_hours_start or current_time <= preferences.quiet_hours_end
        else:
            # Overnight quiet hours (e.g., 22:00 to 08:00)
            return preferences.quiet_hours_start <= current_time <= preferences.quiet_hours_end
    
    def send_sms(self, notification):
        """Send SMS notification via Twilio with retry logic"""
        if not self.twilio_client:
            logger.error(f"Twilio not configured for notification {notification.id}")
            notification.mark_as_failed("Twilio not configured")
            return False
        
        try:
            # Format phone number
            phone_number = notification.user.phone_number
            if not phone_number.startswith('+'):
                phone_number = f"+1{phone_number}"  # Assume US number if no country code
            
            message = self.twilio_client.messages.create(
                body=notification.message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number,
                status_callback=f"{settings.BASE_URL}/api/notifications/twilio-webhook/"
            )
            
            notification.mark_as_sent(message.sid)
            self.log_notification_action(notification, 'sent', f"Twilio SID: {message.sid}")
            
            logger.info(f"SMS sent successfully to {phone_number} - SID: {message.sid}")
            return True
            
        except TwilioException as e:
            error_msg = f"Twilio error: {str(e)}"
            logger.error(f"SMS sending failed for notification {notification.id}: {error_msg}")
            
            # Schedule retry for certain error types
            if e.code in [20003, 20429, 21610]:  # Rate limit, queue full, etc.
                if notification.schedule_retry():
                    self.log_notification_action(notification, 'retry_scheduled', error_msg)
                    return False
            
            notification.mark_as_failed(error_msg)
            self.log_notification_action(notification, 'failed', error_msg)
            return False
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"SMS sending failed for notification {notification.id}: {error_msg}")
            notification.mark_as_failed(error_msg)
            self.log_notification_action(notification, 'failed', error_msg)
            return False
    
    def send_email(self, notification):
        """Send email notification with HTML template"""
        try:
            # Use template if available
            template_name = f"notifications/{notification.type}.html"
            
            context = {
                'user': notification.user,
                'title': notification.title,
                'message': notification.message,
                'notification': notification,
            }
            
            try:
                html_message = render_to_string(template_name, context)
            except:
                html_message = f"<h2>{notification.title}</h2><p>{notification.message}</p>"
            
            send_mail(
                subject=notification.title,
                message=notification.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            notification.mark_as_sent()
            self.log_notification_action(notification, 'sent', f"Email sent to {notification.user.email}")
            
            logger.info(f"Email sent successfully to {notification.user.email}")
            return True
            
        except Exception as e:
            error_msg = f"Email error: {str(e)}"
            logger.error(f"Email sending failed for notification {notification.id}: {error_msg}")
            
            if notification.schedule_retry():
                self.log_notification_action(notification, 'retry_scheduled', error_msg)
                return False
            
            notification.mark_as_failed(error_msg)
            self.log_notification_action(notification, 'failed', error_msg)
            return False
    
    def send_websocket(self, notification):
        """Send real-time notification via WebSocket"""
        if not self.channel_layer:
            logger.warning("Channel layer not configured for WebSocket notifications")
            return False
        
        try:
            # Send to user's personal channel
            user_channel = f"user_{notification.user.id}"
            
            message_data = {
                'type': 'notification_message',
                'notification': {
                    'id': notification.id,
                    'type': notification.type,
                    'title': notification.title,
                    'message': notification.message,
                    'created_at': notification.created_at.isoformat(),
                }
            }
            
            async_to_sync(self.channel_layer.group_send)(
                user_channel,
                message_data
            )
            
            notification.mark_as_sent()
            self.log_notification_action(notification, 'sent', f"WebSocket sent to user_{notification.user.id}")
            
            logger.info(f"WebSocket notification sent to user {notification.user.id}")
            return True
            
        except Exception as e:
            error_msg = f"WebSocket error: {str(e)}"
            logger.error(f"WebSocket sending failed for notification {notification.id}: {error_msg}")
            notification.mark_as_failed(error_msg)
            self.log_notification_action(notification, 'failed', error_msg)
            return False
    
    def send_notification(self, notification):
        """Send notification via appropriate channel"""
        # Check quiet hours for non-emergency notifications
        if notification.type != 'emergency_alert' and self.is_quiet_hours(notification.user):
            # Schedule for after quiet hours
            preferences = self.get_user_preferences(notification.user)
            tomorrow = timezone.now().date() + timezone.timedelta(days=1)
            notification.scheduled_for = timezone.datetime.combine(tomorrow, preferences.quiet_hours_end)
            notification.save()
            return True
        
        success = False
        
        if notification.channel == 'sms':
            success = self.send_sms(notification)
        elif notification.channel == 'email':
            success = self.send_email(notification)
        elif notification.channel == 'websocket':
            success = self.send_websocket(notification)
        elif notification.channel == 'push':
            # TODO: Implement push notifications
            logger.info(f"Push notification not implemented for {notification.id}")
            success = self.send_websocket(notification)  # Fallback to WebSocket
        
        return success
    
    def create_notification_from_template(self, user, template_name, context, channel=None, scheduled_for=None):
        """Create notification using template"""
        try:
            template = NotificationTemplate.objects.get(name=template_name, is_active=True)
            
            # Determine channel based on user preferences if not specified
            if not channel:
                preferences = self.get_user_preferences(user)
                channel_mapping = {
                    'queue_update': preferences.queue_updates,
                    'appointment_reminder': preferences.appointment_reminders,
                    'delay_alert': preferences.delay_alerts,
                    'test_ready': preferences.test_results,
                }
                channel = channel_mapping.get(template.type, 'sms')
            
            # Render template
            title, message = template.render(context)
            
            # Create notification
            notification = Notification.objects.create(
                user=user,
                type=template.type,
                channel=channel,
                title=title,
                message=message,
                scheduled_for=scheduled_for
            )
            
            self.log_notification_action(notification, 'created', f"From template: {template_name}")
            
            # Send immediately if not scheduled
            if not scheduled_for:
                self.send_notification(notification)
            
            return notification
            
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Template {template_name} not found")
            return None
        except Exception as e:
            logger.error(f"Error creating notification from template {template_name}: {str(e)}")
            return None
    
    def create_and_send_notification(self, user, notification_type, title, message, channel='sms', scheduled_for=None):
        """Create notification record and send it"""
        notification = Notification.objects.create(
            user=user,
            type=notification_type,
            channel=channel,
            title=title,
            message=message,
            scheduled_for=scheduled_for
        )
        
        self.log_notification_action(notification, 'created')
        
        # Send immediately if not scheduled
        if not scheduled_for:
            self.send_notification(notification)
        
        return notification
    
    def process_scheduled_notifications(self):
        """Process notifications scheduled for sending"""
        due_notifications = Notification.objects.filter(
            status='pending',
            scheduled_for__lte=timezone.now()
        )
        
        for notification in due_notifications:
            self.send_notification(notification)
    
    def process_retry_notifications(self):
        """Process notifications scheduled for retry"""
        retry_notifications = Notification.objects.filter(
            status='retry',
            next_retry_at__lte=timezone.now()
        )
        
        for notification in retry_notifications:
            self.send_notification(notification)
    
    def log_notification_action(self, notification, action, details=''):
        """Log notification action for audit trail"""
        NotificationLog.objects.create(
            notification=notification,
            action=action,
            details=details
        )
    
    def send_queue_position_update(self, queue_entry):
        """Send notification about queue position update"""
        context = {
            'patient_name': queue_entry.patient.user.get_full_name(),
            'queue_name': queue_entry.queue.name,
            'position': queue_entry.position,
            'estimated_wait': queue_entry.queue.estimated_wait_time,
        }
        
        return self.create_notification_from_template(
            user=queue_entry.patient.user,
            template_name='queue_position_update',
            context=context
        )
    
    def send_consultation_ready(self, queue_entry):
        """Send notification that patient is ready for consultation"""
        context = {
            'patient_name': queue_entry.patient.user.get_full_name(),
            'queue_name': queue_entry.queue.name,
            'department': queue_entry.queue.department.name,
        }
        
        return self.create_notification_from_template(
            user=queue_entry.patient.user,
            template_name='consultation_ready',
            context=context
        )
    
    def send_delay_notification(self, queue_entry, delay_minutes):
        """Send notification about delays"""
        context = {
            'patient_name': queue_entry.patient.user.get_full_name(),
            'queue_name': queue_entry.queue.name,
            'delay_minutes': delay_minutes,
            'new_estimated_time': queue_entry.estimated_time,
        }
        
        return self.create_notification_from_template(
            user=queue_entry.patient.user,
            template_name='delay_alert',
            context=context
        )
    
    def send_lab_results_ready(self, lab_test):
        """Send notification that lab results are ready"""
        context = {
            'patient_name': lab_test.patient.user.get_full_name(),
            'test_type': lab_test.get_test_type_display(),
            'completed_at': lab_test.completed_at,
        }
        
        return self.create_notification_from_template(
            user=lab_test.patient.user,
            template_name='lab_results_ready',
            context=context,
            channel='email'  # Lab results typically sent via email
        )
