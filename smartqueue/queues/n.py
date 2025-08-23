# queues/views.py
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import PatientQueue, QueueEntry
from .serializers import QueueSerializer, QueueEntrySerializer, QueueJoinSerializer, QueueStatusSerializer
from .throttles import QueueJoinThrottle
from .permissions import CanJoinQueue, IsDepartmentStaff

class QueueList(generics.ListAPIView):
    queryset = PatientQueue.objects.filter(is_active=True)
    serializer_class = QueueSerializer
    permission_classes = [permissions.IsAuthenticated]

class QueueDetail(generics.RetrieveAPIView):
    queryset = PatientQueue.objects.filter(is_active=True)
    serializer_class = QueueSerializer
    permission_classes = [permissions.IsAuthenticated]

class QueueEntriesList(generics.ListAPIView):
    serializer_class = QueueEntrySerializer
    permission_classes = [IsDepartmentStaff]

    def get_queryset(self):
        queue_id = self.kwargs['pk']
        return QueueEntry.objects.filter(queue_id=queue_id).order_by('priority', 'joined_at')

class JoinQueue(generics.CreateAPIView):
    serializer_class = QueueJoinSerializer
    throttle_classes = [QueueJoinThrottle]
    permission_classes = [CanJoinQueue]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        queue = PatientQueue.objects.get(id=serializer.validated_data['queue_id'])
        
        queue_entry = QueueEntry.objects.create(
            queue=queue,
            patient=request.user,
            priority=serializer.validated_data['priority']
        )
        
        response_serializer = QueueEntrySerializer(queue_entry)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class QueueStatus(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            queue = PatientQueue.objects.get(id=pk, is_active=True)
            
            if request.user.role == 'patient':
                # Patients can only see their own status
                user_entry = QueueEntry.objects.filter(
                    queue=queue,
                    patient=request.user,
                    status__in=['waiting', 'processing']
                ).first()
                
                if user_entry:
                    serializer = QueueStatusSerializer(user_entry)
                    return Response(serializer.data)
                return Response({'detail': 'No active queue entry found'}, status=404)
            
            else:
                # Staff can see queue statistics
                data = {
                    'queue_id': queue.id,
                    'department': queue.department.name,
                    'total_entries': queue.queue_entries.count(),
                    'waiting_count': queue.queue_entries.filter(status='waiting').count(),
                    'processing_count': queue.queue_entries.filter(status='processing').count(),
                    'estimated_wait_time': queue.estimated_wait_time
                }
                return Response(data)
                
        except PatientQueue.DoesNotExist:
            return Response({'detail': 'Queue not found'}, status=404)

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