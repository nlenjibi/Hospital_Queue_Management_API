
from django.urls import path
from . import views

urlpatterns = [
    # Queue management endpoints
    path('', views.QueueList.as_view(), name='queue-list'),
    path('<int:pk>/', views.QueueDetail.as_view(), name='queue-detail'),
    path('<int:pk>/join/', views.JoinQueue.as_view(), name='join-queue'),
    path('<int:pk>/status/', views.QueueStatus.as_view(), name='queue-status'),
    path('<int:pk>/entries/', views.QueueEntriesList.as_view(), name='queue-entries'),
    path('entries/<int:entry_id>/update/', views.UpdateQueueEntry.as_view(), name='update-queue-entry'),
]