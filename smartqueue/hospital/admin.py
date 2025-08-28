from django.contrib import admin
# Register your models here.
from .models import Department, Staff

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
	list_display = ('name', 'department_type', 'is_active', 'created_at')
	search_fields = ('name', 'department_type')
	list_filter = ('department_type', 'is_active')

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
	list_display = ('user', 'department', 'role', 'specialty', 'is_on_break', 'is_primary', 'can_manage_queue')
	search_fields = ('user__username', 'department__name', 'role', 'specialty', 'license_number')
	list_filter = ('role', 'specialty', 'department', 'is_on_break', 'is_primary', 'can_manage_queue')

# Register your models here.
