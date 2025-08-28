
from django.contrib import admin
from .models import Queue, QueueEntry, QueueAnalytics

@admin.register(Queue)
class QueueAdmin(admin.ModelAdmin):
	list_display = ('name', 'department', 'is_active', 'max_capacity', 'avg_processing_time', 'created_at')
	search_fields = ('name', 'department__name')
	list_filter = ('department', 'is_active')

@admin.register(QueueEntry)
class QueueEntryAdmin(admin.ModelAdmin):
	list_display = ('patient', 'queue', 'status', 'position', 'joined_at', 'called_at', 'completed_at')
	search_fields = ('patient__user__username', 'queue__name', 'status')
	list_filter = ('status', 'queue')

@admin.register(QueueAnalytics)
class QueueAnalyticsAdmin(admin.ModelAdmin):
	list_display = ('queue', 'date', 'total_patients', 'avg_wait_time', 'avg_processing_time', 'no_show_count')
	search_fields = ('queue__name',)
	list_filter = ('queue', 'date')
