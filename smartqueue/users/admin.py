
from django.contrib import admin
from .models import User, Patient

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
	list_display = ('username', 'email', 'role', 'phone_number', 'is_active', 'is_staff', 'created_at')
	search_fields = ('username', 'email', 'role', 'phone_number')
	list_filter = ('role', 'is_active', 'is_staff')

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
	list_display = ('user', 'medical_id', 'priority_level', 'date_of_birth', 'emergency_contact')
	search_fields = ('user__username', 'medical_id', 'priority_level', 'emergency_contact')
	list_filter = ('priority_level',)
