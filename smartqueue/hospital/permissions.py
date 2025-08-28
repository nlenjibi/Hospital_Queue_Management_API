from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsDepartmentAdmin(BasePermission):
    """
    Allows access only to users with admin or superadmin role for department management.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'superadmin']

class IsStaffOrReadOnly(BasePermission):
    """
    Allows staff (doctor, nurse, staff) full access, others read-only.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role in ['doctor', 'nurse', 'staff']

class IsDepartmentMember(BasePermission):
    """
    Allows access only to staff assigned to the department.
    """
    def has_object_permission(self, request, view, obj):
        # obj can be Department or Staff
        if hasattr(obj, 'department'):
            return obj.department in request.user.staff_set.all().values_list('department', flat=True)
        return