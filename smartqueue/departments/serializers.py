# departments/serializers.py
from rest_framework import serializers
from .models import Department, DepartmentStaff
from django.conf import settings

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'department_type', 'description', 'is_active']

class DepartmentStaffSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.username', read_only=True)
    staff_email = serializers.CharField(source='staff.email', read_only=True)
    
    class Meta:
        model = DepartmentStaff
        fields = ['id', 'staff', 'staff_name', 'staff_email', 'department', 'is_primary', 'can_manage_queue']