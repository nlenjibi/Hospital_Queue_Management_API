
from django.contrib import admin
from .models import (
	LabDepartment, LabTechnician, LabEquipment, LabTest, LabTestTemplate,
	LabSchedule, LabAnalytics
)

@admin.register(LabDepartment)
class LabDepartmentAdmin(admin.ModelAdmin):
	list_display = ('name', 'location', 'phone_number', 'is_active')
	search_fields = ('name', 'location', 'phone_number')
	list_filter = ('is_active',)

@admin.register(LabTechnician)
class LabTechnicianAdmin(admin.ModelAdmin):
	list_display = ('staff', 'lab_department', 'specialization', 'is_available')
	search_fields = ('staff__user__username', 'lab_department__name', 'specialization', 'license_number')
	list_filter = ('specialization', 'is_available', 'lab_department')

@admin.register(LabEquipment)
class LabEquipmentAdmin(admin.ModelAdmin):
	list_display = ('name', 'model', 'serial_number', 'lab_department', 'status')
	search_fields = ('name', 'model', 'serial_number')
	list_filter = ('status', 'lab_department')

@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
	list_display = ('patient', 'test_type', 'priority', 'status', 'lab_department', 'ordered_at')
	search_fields = ('patient__user__username', 'test_type', 'lab_department__name')
	list_filter = ('priority', 'status', 'lab_department')

@admin.register(LabTestTemplate)
class LabTestTemplateAdmin(admin.ModelAdmin):
	list_display = ('name', 'test_type', 'lab_department', 'estimated_duration', 'is_active')
	search_fields = ('name', 'test_type', 'lab_department__name')
	list_filter = ('test_type', 'lab_department', 'is_active')

@admin.register(LabSchedule)
class LabScheduleAdmin(admin.ModelAdmin):
	list_display = ('lab_test', 'technician', 'scheduled_date', 'scheduled_time', 'duration_minutes')
	search_fields = ('lab_test__patient__user__username', 'technician__staff__user__username')
	list_filter = ('scheduled_date', 'technician')

@admin.register(LabAnalytics)
class LabAnalyticsAdmin(admin.ModelAdmin):
	list_display = ('lab_department', 'date', 'total_tests_ordered', 'tests_completed', 'tests_pending', 'tests_overdue')
	search_fields = ('lab_department__name',)
	list_filter = ('lab_department', 'date')
