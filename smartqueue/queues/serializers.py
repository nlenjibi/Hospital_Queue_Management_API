from rest_framework import serializers
from .models import Queue, QueueEntry, QueueAnalytics
from users.serializers import PatientSerializer
from hospital.serializers import DepartmentSerializer

# Serializer for Queue model with department details and calculated fields
class QueueSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    current_length = serializers.ReadOnlyField()
    estimated_wait_time = serializers.ReadOnlyField()

    class Meta:
        model = Queue
        fields = [
            'id', 'department', 'name', 'is_active', 'max_capacity',
            'avg_processing_time', 'created_at', 'updated_at',
            'current_length', 'estimated_wait_time'
        ]

# Serializer for creating/joining a queue entry with validation
class QueueEntryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueueEntry
        fields = ['patient', 'queue', 'status']

    def validate(self, data):
        # Prevent duplicate active queue entry for the same patient in the same queue
        patient = data.get('patient')
        queue = data.get('queue')
        if QueueEntry.objects.filter(
            patient=patient,
            queue=queue,
            status__in=['waiting', 'in_progress']
        ).exists():
            raise serializers.ValidationError("Patient is already in this queue.")
        return data

    def create(self, validated_data):
        # Optionally set patient from request context if not provided
        request = self.context.get('request')
        if request and request.user.is_authenticated and hasattr(request.user, 'patient_profile'):
            validated_data['patient'] = request.user.patient_profile
        return super().create(validated_data)

# Serializer for QueueEntry model with patient and queue details
class QueueEntrySerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    queue = QueueSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    position = serializers.IntegerField(read_only=True)
    joined_at = serializers.DateTimeField(read_only=True)
    called_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True)
    estimated_time = serializers.DateTimeField(read_only=True)

    class Meta:
        model = QueueEntry
        fields = [
            'id', 'patient', 'queue', 'status', 'status_display', 'position',
            'joined_at', 'called_at', 'completed_at', 'estimated_time',
            'actual_wait_time', 'consultation_start', 'notes'
        ]

# Serializer for joining a queue with priority (for custom endpoints)
class JoinQueueSerializer(serializers.Serializer):
    queue_id = serializers.IntegerField()
    priority = serializers.ChoiceField(
        choices=[('emergency', 'Emergency'), ('appointment', 'Appointment'), ('walk_in', 'Walk-in')],
        default='walk_in'
    )

    def validate_queue_id(self, value):
        # Ensure queue exists and is active
        try:
            queue = Queue.objects.get(id=value, is_active=True)
        except Queue.DoesNotExist:
            raise serializers.ValidationError("Queue not found or inactive")
        return value

# Serializer for queue entry status and estimated wait
class QueueStatusSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.user.username', read_only=True)
    current_position = serializers.IntegerField(source='position', read_only=True)
    estimated_wait = serializers.SerializerMethodField()

    class Meta:
        model = QueueEntry
        fields = [
            'id', 'patient_name', 'current_position', 'status',
            'estimated_wait', 'joined_at'
        ]

    def get_estimated_wait(self, obj):
        # Calculate estimated wait time for this entry
        queue = obj.queue
        active_ahead = QueueEntry.objects.filter(
            queue=queue,
            status='waiting',
            position__lt=obj.position
        ).count()
        return active_ahead * queue.avg_processing_time

# Serializer for queue analytics/statistics
class QueueAnalyticsSerializer(serializers.ModelSerializer):
    queue_name = serializers.CharField(source='queue.name', read_only=True)

    class Meta:
        model = QueueAnalytics
        fields = [
            'id', 'queue', 'queue_name', 'date', 'total_patients',
            'avg_wait_time', 'avg_processing_time', 'no_show_count',
            'peak_hour_start', 'peak_hour_end'
        ]