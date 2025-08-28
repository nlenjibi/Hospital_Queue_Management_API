from rest_framework import serializers
from .models import Notification, NotificationPreference, NotificationTemplate

class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'channel', 'title', 'message', 'status',
            'sent_at', 'delivered_at', 'read_at', 'is_read',
            'retry_count', 'created_at'
        ]
    
    def get_is_read(self, obj):
        return obj.read_at is not None

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'queue_updates', 'appointment_reminders', 'delay_alerts', 'test_results',
            'reminder_minutes_before', 'quiet_hours_start', 'quiet_hours_end'
        ]

class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = '__all__'
