
from rest_framework import permissions

class IsDepartmentStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Admins can do anything
        if request.user.role == 'admin':
            return True
        
        # Check if user is staff in the department
        department_id = view.kwargs.get('department_id')
        if department_id:
            from departments.models import DepartmentStaff
            return DepartmentStaff.objects.filter(
                staff=request.user,
                department_id=department_id
            ).exists()
        
        return False

class CanJoinQueue(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'patient'