
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .models import PatientQueue, QueueEntry
from .serializers import QueueSerializer, QueueEntrySerializer, QueueJoinSerializer, QueueStatusSerializer
from .throttles import QueueJoinThrottle
from .permissions import CanJoinQueue, IsDepartmentStaff



class QueueList(generics.ListCreateAPIView):
    queryset = PatientQueue.objects.filter(is_active=True)
    serializer_class = QueueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Staff can see all queues, patients see only relevant ones
        if self.request.user.role in ['doctor', 'nurse', 'admin']:
            return PatientQueue.objects.filter(is_active=True)
        return PatientQueue.objects.none()  # Patients don't need to see queue list
class QueueDetail(generics.RetrieveAPIView):
    queryset = PatientQueue.objects.filter(is_active=True)
    serializer_class = QueueSerializer
    permission_classes = [IsAuthenticated]

class QueueEntriesList(generics.ListAPIView):
    serializer_class = QueueEntrySerializer
    permission_classes = [IsDepartmentStaff]

    def get_queryset(self):
        queue_id = self.kwargs['pk']
        return QueueEntry.objects.filter(queue_id=queue_id).order_by('priority', 'joined_at')

class JoinQueue(generics.CreateAPIView):
    queryset = QueueEntry.objects.all()
    serializer_class = QueueJoinSerializer
    throttle_classes = [QueueJoinThrottle]
    permission_classes = [CanJoinQueue, IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        queue = PatientQueue.objects.get(id=serializer.validated_data['queue_id'])
        
        # Create queue entry
        queue_entry = QueueEntry.objects.create(
            queue=queue,
            patient=request.user,
            priority=serializer.validated_data['priority']
        )
        
        # Return the created entry
        response_serializer = QueueEntrySerializer(queue_entry)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class QueueStatus(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            queue = PatientQueue.objects.get(id=pk, is_active=True)
        except PatientQueue.DoesNotExist:
            return Response({'detail': 'Queue not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role == 'patient':
            entry = QueueEntry.objects.filter(
                queue=queue,
                patient=request.user,
                status__in=['waiting', 'processing']
            ).first()
            if entry:
                serializer = QueueStatusSerializer(entry)
                return Response(serializer.data)
            return Response({'detail': 'No active queue entry found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            data = {
                'queue_id': queue.id,
                'department': queue.department.name,
                'total_entries': queue.queue_entries.count(),
                'waiting_count': queue.queue_entries.filter(status='waiting').count(),
                'processing_count': queue.queue_entries.filter(status='processing').count(),
                'estimated_wait_time': queue.estimated_wait_time
            }
            return Response(data)
     
class UpdateQueueEntry(generics.UpdateAPIView):
    queryset = QueueEntry.objects.all()
    serializer_class = QueueEntrySerializer
    permission_classes = [IsDepartmentStaff]
    lookup_field = 'id'
    lookup_url_kwarg = 'entry_id'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Only allow status updates for staff
        if 'status' in request.data:
            instance.status = request.data['status']
            if request.data['status'] == 'processing':
                instance.called_at = timezone.now()
            elif request.data['status'] == 'completed':
                instance.completed_at = timezone.now()
            instance.save()
            
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        
        return Response({'detail': 'Only status updates are allowed'}, status=400)       