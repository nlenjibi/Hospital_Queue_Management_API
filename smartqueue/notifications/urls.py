from django.urls import path
from . import views

urlpatterns = [
    # Notification list and detail
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),

    # Mark notification as read
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='notification-mark-read'),
    path('notifications/mark-all-read/', views.mark_all_read, name='notification-mark-all-read'),
    path('notifications/unread-count/', views.unread_count, name='notification-unread-count'),

    # Send notification (admin/staff)
    path('notifications/send/', views.send_notification, name='notification-send'),
    path('notifications/send-test/', views.send_test_notification, name='notification-send-test'),

    # Notification preferences
    path('preferences/', views.NotificationPreferenceView.as_view(), name='notification-preferences'),

    # Twilio webhook
    path('twilio-webhook/', views.twilio_webhook, name='twilio-webhook'),

    # Admin: process scheduled/retry notifications
    path('process-scheduled/', views.process_scheduled_notifications, name='process-scheduled-notifications'),
]
