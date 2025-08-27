from rest_framework import serializers
from .models import Department, Staff
from users.serializers import UserSerializer

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'department_type', 'description', 'is_active', 'created_at']

class StaffSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    is_available = serializers.ReadOnlyField()

    class Meta:
        model = Staff
        fields = [
            'id', 'user', 'department', 'department_name', 'role', 'specialty',
            'license_number', 'shift_start', 'shift_end', 'is_on_break',
            'avg_consultation_time', 'is_primary', 'can_manage_queue', 'is_available'
        ]

