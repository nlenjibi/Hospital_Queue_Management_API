from rest_framework import permissions

class CanOrderLabTest(permissions.BasePermission):
    """
    Allows only doctors, nurses, or staff to order lab tests.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            getattr(request.user, 'role', None) in ['doctor', 'nurse', 'staff', 'admin', 'superadmin']
        )

class CanManageLab(permissions.BasePermission):
    """
    Allows only lab technicians, admin, or superadmin to manage lab operations.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            getattr(request.user, 'role', None) in ['lab_technician', 'admin', 'superadmin']
        )

class IsLabDepartmentMember(permissions.BasePermission):
    """
    Allows access only to users assigned to the lab department.
    """
    def has_object_permission(self, request, view, obj):
        # obj can be LabDepartment, LabTest, etc.
        if hasattr(obj, 'lab_department'):
            return hasattr(request.user, 'staff_profile') and (
                obj.lab_department == request.user.staff_profile.lab_department
            )
        return False

class CanViewLabResults(permissions.BasePermission):
    """
    Allows patients to view their own lab results, and staff/admin to view any.
    """
    def has_object_permission(self, request, view, obj):
        # obj is LabTest
        if getattr(request.user, 'role', None) == 'patient':
            return obj.patient.user == request.user
        return getattr(request.user, 'role', None) in ['doctor', 'nurse', 'staff', 'admin', 'superadmin']