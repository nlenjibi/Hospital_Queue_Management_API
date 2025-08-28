from django.db import models
from django.utils import timezone
from users.models import User

class NotificationPreference(models.Model):
    CHANNEL_CHOICES = [
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
        ('all', 'All Channels'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    queue_updates = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='sms')
    appointment_reminders = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='sms')
    delay_alerts = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='sms')
    test_results = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='email')
    
    # Timing preferences
    reminder_minutes_before = models.IntegerField(default=15)  # Minutes before appointment
    quiet_hours_start = models.TimeField(default='22:00')
    quiet_hours_end = models.TimeField(default='08:00')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - Notification Preferences"

class Notification(models.Model):
    TYPE_CHOICES = [
        ('queue_update', 'Queue Update'),
        ('appointment_reminder', 'Appointment Reminder'),
        ('test_ready', 'Test Ready'),
        ('delay_alert', 'Delay Alert'),
        ('emergency_alert', 'Emergency Alert'),
        ('consultation_ready', 'Consultation Ready'),
        ('lab_results', 'Lab Results'),
    ]
    
    CHANNEL_CHOICES = [
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
        ('websocket', 'WebSocket'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('retry', 'Retry'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Delivery tracking
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Retry logic
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    # External service tracking
    external_id = models.CharField(max_length=100, blank=True)  # Twilio SID, etc.
    error_message = models.TextField(blank=True)
    
    # Scheduling
    scheduled_for = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.type} ({self.status})"
    
    def mark_as_sent(self, external_id=None):
        self.status = 'sent'
        self.sent_at = timezone.now()
        if external_id:
            self.external_id = external_id
        self.save()
    
    def mark_as_failed(self, error_message=None):
        self.status = 'failed'
        if error_message:
            self.error_message = error_message
        self.save()
    
    def schedule_retry(self, minutes=5):
        if self.retry_count < self.max_retries:
            self.status = 'retry'
            self.retry_count += 1
            self.next_retry_at = timezone.now() + timezone.timedelta(minutes=minutes * self.retry_count)
            self.save()
            return True
        return False

class NotificationTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=20, choices=Notification.TYPE_CHOICES)
    channel = models.CharField(max_length=10, choices=Notification.CHANNEL_CHOICES)
    
    title_template = models.CharField(max_length=200)
    message_template = models.TextField()
    
    # Template variables documentation
    variables = models.JSONField(default=dict, help_text="Available template variables")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.type} ({self.channel})"
    
    def render(self, context):
        """Render template with context variables"""
        title = self.title_template
        message = self.message_template
        
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            title = title.replace(placeholder, str(value))
            message = message.replace(placeholder, str(value))
        
        return title, message

class NotificationLog(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)  # 'sent', 'failed', 'retry', 'delivered', 'read'
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.notification.id} - {self.action} at {self.timestamp}"
