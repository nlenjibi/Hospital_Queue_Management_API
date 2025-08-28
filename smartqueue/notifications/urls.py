from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('preferences/', views.NotificationPreferenceView.as_view(), name='notification_preferences'),
    path('<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('unread-count/', views.unread_count, name='unread_count'),
    path('test/', views.send_test_notification, name='send_test_notification'),
    path('twilio-webhook/', views.twilio_webhook, name='twilio_webhook'),
    path('process-scheduled/', views.process_scheduled_notifications, name='process_scheduled'),
]
