from django.urls import path
from . import views

urlpatterns = [
    # List all queues or create a new one (admin/staff only for create)
    path('', views.QueueListCreateView.as_view(), name='queue_list'),

    # Patient joins a queue (throttled, permission checked)
    path('join/', views.join_queue, name='join_queue'),

    # Get estimated wait time for a queue
    path('wait-time/', views.get_wait_time, name='wait_time'),

    # Get all queue entries for the current patient
    path('my-entries/', views.MyQueueEntriesView.as_view(), name='my_queue_entries'),

    # Staff calls the next patient in a queue
    path('<int:queue_id>/call-next/', views.call_next_patient, name='call_next_patient'),

    # Staff marks a queue entry as completed
    path('entry/<int:entry_id>/complete/', views.complete_consultation, name='complete_consultation'),

    # Staff sends a patient to lab
    path('entry/<int:entry_id>/send-to-lab/', views.send_to_lab, name='send_to_lab'),

    # Get analytics for a specific queue (admin/staff only)
    path('<int:queue_id>/analytics/', views.queue_analytics, name='queue_analytics'),

    # Run all queue maintenance tasks (admin/staff only)
    path('maintenance/', views.run_maintenance, name='run_maintenance'),
]
