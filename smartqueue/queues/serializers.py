# queues/serializers.py
from rest_framework import serializers
from .models import PatientQueue, QueueEntry
from departments.models import Department
from django.conf import settings

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'department_type', 'description']

class QueueSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        write_only=True,
        source='department'
    )
    active_count = serializers.SerializerMethodField()
    estimated_wait = serializers.SerializerMethodField()

    class Meta:
        model = PatientQueue
        fields = [
            'id', 'department', 'department_id', 'current_position',
            'is_active', 'max_capacity', 'estimated_wait_time',
            'active_count', 'estimated_wait', 'created_at', 'updated_at'
        ]
        read_only_fields = ['current_position', 'created_at', 'updated_at']

    def get_active_count(self, obj):
        return obj.get_active_count()

    def get_estimated_wait(self, obj):
        # Calculate estimated wait based on queue length and processing time
        active_count = obj.get_active_count()
        return active_count * obj.estimated_wait_time

class QueueEntrySerializer(serializers.ModelSerializer):
    queue = QueueSerializer(read_only=True)
    queue_id = serializers.PrimaryKeyRelatedField(
        queryset=PatientQueue.objects.all(),
        write_only=True,
        source='queue'
    )
    patient_name = serializers.CharField(source='patient.username', read_only=True)
    patient_email = serializers.CharField(source='patient.email', read_only=True)
    department_name = serializers.CharField(source='queue.department.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = QueueEntry
        fields = [
            'id', 'queue', 'queue_id', 'patient', 'patient_name', 'patient_email',
            'priority', 'priority_display', 'status', 'status_display',
            'position', 'department_name', 'joined_at', 'called_at', 'completed_at'
        ]
        read_only_fields = ['position', 'joined_at', 'called_at', 'completed_at']

    def validate(self, data):
        # Check if patient is already in an active queue
        patient = data.get('patient')
        queue = data.get('queue')
        
        if QueueEntry.objects.filter(
            patient=patient,
            queue=queue,
            status__in=['waiting', 'processing']
        ).exists():
            raise serializers.ValidationError("Patient is already in this queue")
        
        return data

    def create(self, validated_data):
        # Set the patient from the request user if not provided
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.role == 'patient':
                validated_data['patient'] = request.user
        
        return super().create(validated_data)

class QueueJoinSerializer(serializers.Serializer):
    queue_id = serializers.IntegerField()
    priority = serializers.IntegerField(
        min_value=0,
        max_value=3,
        default=2
    )

    def validate_queue_id(self, value):
        try:
            queue = PatientQueue.objects.get(id=value, is_active=True)
        except PatientQueue.DoesNotExist:
            raise serializers.ValidationError("Queue not found or inactive")
        return value

class QueueStatusSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.username', read_only=True)
    current_position = serializers.IntegerField(source='position', read_only=True)
    estimated_wait = serializers.SerializerMethodField()

    class Meta:
        model = QueueEntry
        fields = [
            'id', 'patient_name', 'current_position', 'status',
            'estimated_wait', 'joined_at'
        ]

    def get_estimated_wait(self, obj):
        queue = obj.queue
        active_ahead = QueueEntry.objects.filter(
            queue=queue,
            status__in=['waiting', 'processing'],
            priority__lte=obj.priority,
            joined_at__lt=obj.joined_at
        ).count()
        return active_ahead * queue.estimated_wait_time