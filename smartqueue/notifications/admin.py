
from django.contrib import admin
from .models import Notification, NotificationPreference, NotificationTemplate, NotificationLog

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = ('user', 'type', 'channel', 'status', 'sent_at', 'delivered_at', 'read_at', 'created_at')
	search_fields = ('user__username', 'type', 'channel', 'title', 'message')
	list_filter = ('type', 'channel', 'status', 'created_at')

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
	list_display = ('user', 'queue_updates', 'appointment_reminders', 'delay_alerts', 'test_results', 'reminder_minutes_before', 'quiet_hours_start', 'quiet_hours_end')
	search_fields = ('user__username',)

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
	list_display = ('name', 'type', 'channel', 'is_active', 'created_at')
	search_fields = ('name', 'type', 'channel')
	list_filter = ('type', 'channel', 'is_active')

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
	list_display = ('notification', 'action', 'details', 'timestamp')
	search_fields = ('notification__id', 'action', 'details')
	list_filter = ('action', 'timestamp')
