from rest_framework import serializers
from .models import LabTest, LabDepartment, LabTechnician, LabSchedule, LabEquipment
from users.serializers import PatientSerializer
from hospital.serializers import StaffSerializer

class LabDepartmentSerializer(serializers.ModelSerializer):
    is_open = serializers.ReadOnlyField()
    
    class Meta:
        model = LabDepartment
        fields = '__all__'

class LabTechnicianSerializer(serializers.ModelSerializer):
    staff = StaffSerializer(read_only=True)
    
    class Meta:
        model = LabTechnician
        fields = '__all__'

class LabEquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabEquipment
        fields = '__all__'

class LabTestSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    ordered_by = StaffSerializer(read_only=True)
    assigned_technician = LabTechnicianSerializer(read_only=True)
    lab_department = LabDepartmentSerializer(read_only=True)
    equipment_used = LabEquipmentSerializer(read_only=True)
    reviewed_by = StaffSerializer(read_only=True)
    estimated_completion_time = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = LabTest
        fields = '__all__'

class LabTestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTest
        fields = [
            'patient', 'test_type', 'priority', 'clinical_notes',
            'lab_department', 'queue_reentry'
        ]

    def validate(self, data):
        # Ensure lab department is active
        lab_department = data.get('lab_department')
        if lab_department and not lab_department.is_active:
            raise serializers.ValidationError("Selected lab department is not active.")
        return data

class LabScheduleSerializer(serializers.ModelSerializer):
    lab_test = LabTestSerializer(read_only=True)
    technician = LabTechnicianSerializer(read_only=True)
    equipment = LabEquipmentSerializer(read_only=True)
    
    class Meta:
        model = LabSchedule
        fields = '__all__'

    def validate(self, data):
        technician = data.get('technician')
        scheduled_date = data.get('scheduled_date')
        scheduled_time = data.get('scheduled_time')
        if technician and scheduled_date and scheduled_time:
            exists = LabSchedule.objects.filter(
                technician=technician,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time
            ).exists()
            if exists:
                raise serializers.ValidationError("Technician is already scheduled for this time.")
        return data
