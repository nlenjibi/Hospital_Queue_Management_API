from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Queue, QueueEntry, QueueAnalytics
from .serializers import (
    QueueSerializer, QueueEntrySerializer, JoinQueueSerializer, QueueAnalyticsSerializer
)
from .services import QueueManagementService
from .permissions import CanJoinQueue, CanManageQueue
from .throttles import QueueJoinThrottle
from users.models import Patient
from hospital.models import Staff

queue_service = QueueManagementService()

class QueueListCreateView(generics.ListCreateAPIView):
    queryset = Queue.objects.filter(is_active=True)
    serializer_class = QueueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Queue.objects.filter(is_active=True)
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        return queryset.order_by('name')

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanJoinQueue])
@throttle_classes([QueueJoinThrottle])
def join_queue(request):
    """
    Patient endpoint to join a queue.
    Uses QueueManagementService for emergency and notifications.
    """
    serializer = JoinQueueSerializer(data=request.data)
    if serializer.is_valid():
        queue_id = serializer.validated_data['queue_id']
        priority = serializer.validated_data.get('priority', 'walk_in')
        try:
            queue = Queue.objects.get(id=queue_id, is_active=True)
            patient = Patient.objects.get(user=request.user)
            # Check if patient is already in this queue
            existing_entry = QueueEntry.objects.filter(
                patient=patient,
                queue=queue,
                status__in=['waiting', 'in_progress', 'in_test']
            ).first()
            if existing_entry:
                return Response({'error': 'Already in this queue'}, status=status.HTTP_400_BAD_REQUEST)
            # Check queue capacity
            if queue.current_length >= queue.max_capacity:
                return Response({'error': 'Queue is full'}, status=status.HTTP_400_BAD_REQUEST)
            # Set patient priority if provided
            if patient.priority_level != priority:
                patient.priority_level = priority
                patient.save()
            # Use service for emergency
            if priority == 'emergency':
                entry = queue_service.handle_emergency_patient(patient, queue)
            else:
                entry = QueueEntry.objects.create(
                    patient=patient,
                    queue=queue
                )
            # Use service to send notifications
            queue_service.send_queue_notifications()
            return Response(QueueEntrySerializer(entry).data, status=status.HTTP_201_CREATED)
        except Queue.DoesNotExist:
            return Response({'error': 'Queue not found'}, status=status.HTTP_404_NOT_FOUND)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient profile not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wait_time(request):
    """
    Get estimated wait time for a queue.
    """
    queue_id = request.query_params.get('queue_id')
    if not queue_id:
        return Response({'error': 'queue_id required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        queue = Queue.objects.get(id=queue_id)
        return Response({
            'queue_id': queue.id,
            'estimated_wait_time': queue.estimated_wait_time,
            'current_length': queue.current_length,
            'next_patient_eta': queue.get_next_patient().estimated_time if queue.get_next_patient() else None
        })
    except Queue.DoesNotExist:
        return Response({'error': 'Queue not found'}, status=status.HTTP_404_NOT_FOUND)

class MyQueueEntriesView(generics.ListAPIView):
    serializer_class = QueueEntrySerializer
    permission_classes = [IsAuthenticated, CanJoinQueue]

    def get_queryset(self):
        try:
            patient = Patient.objects.get(user=self.request.user)
            return QueueEntry.objects.filter(
                patient=patient,
                status__in=['waiting', 'in_progress', 'in_test']
            ).order_by('position')
        except Patient.DoesNotExist:
            return QueueEntry.objects.none()

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageQueue])
def call_next_patient(request, queue_id):
    """
    Staff endpoint to call the next patient.
    Uses QueueManagementService for notifications.
    """
    try:
        staff = Staff.objects.get(user=request.user)
        queue = Queue.objects.get(id=queue_id, department=staff.department)
        next_entry = queue.get_next_patient()
        if not next_entry:
            return Response({'message': 'No patients waiting'}, status=status.HTTP_200_OK)
        next_entry.call_patient()
        queue_service.send_queue_notifications()
        return Response({
            'message': 'Patient called successfully',
            'patient': QueueEntrySerializer(next_entry).data
        })
    except Staff.DoesNotExist:
        return Response({'error': 'Staff profile not found'}, status=status.HTTP_404_NOT_FOUND)
    except Queue.DoesNotExist:
        return Response({'error': 'Queue not found or access denied'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageQueue])
def complete_consultation(request, entry_id):
    """
    Staff endpoint to mark consultation as complete.
    Uses QueueManagementService for analytics update.
    """
    try:
        staff = Staff.objects.get(user=request.user)
        entry = QueueEntry.objects.get(
            id=entry_id,
            queue__department=staff.department,
            status='in_progress'
        )
        entry.complete_consultation()
        queue_service.update_daily_analytics()
        return Response({'message': 'Consultation completed successfully'})
    except Staff.DoesNotExist:
        return Response({'error': 'Staff profile not found'}, status=status.HTTP_404_NOT_FOUND)
    except QueueEntry.DoesNotExist:
        return Response({'error': 'Queue entry not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageQueue])
def send_to_lab(request, entry_id):
    """
    Staff endpoint to send patient to lab.
    Uses QueueManagementService for notifications.
    """
    try:
        staff = Staff.objects.get(user=request.user)
        entry = QueueEntry.objects.get(
            id=entry_id,
            queue__department=staff.department,
            status='in_progress'
        )
        entry.send_to_lab()
        queue_service.send_queue_notifications()
        return Response({'message': 'Patient sent to lab successfully'})
    except Staff.DoesNotExist:
        return Response({'error': 'Staff profile not found'}, status=status.HTTP_404_NOT_FOUND)
    except QueueEntry.DoesNotExist:
        return Response({'error': 'Queue entry not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated, CanManageQueue])
def queue_analytics(request, queue_id):
    """
    Get analytics for a specific queue.
    Uses QueueManagementService for analytics update.
    """
    try:
        queue = Queue.objects.get(id=queue_id)
        queue_service.update_daily_analytics()
        recent_analytics = QueueAnalytics.objects.filter(
            queue=queue
        ).order_by('-date')[:7]  # Last 7 days
        analytics_data = QueueAnalyticsSerializer(recent_analytics, many=True).data
        return Response({
            'queue': QueueSerializer(queue).data,
            'analytics': analytics_data
        })
    except Queue.DoesNotExist:
        return Response({'error': 'Queue not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageQueue])
def run_maintenance(request):
    """
    Admin/staff endpoint to run queue maintenance tasks.
    Uses QueueManagementService for all maintenance.
    """
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    queue_service.run_maintenance_tasks()
    return Response({'message': 'Maintenance tasks completed successfully'})
