from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminUserOrReadOnly(BasePermission):
    """
    Allows full access to admin users, read-only for others.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role in ['admin', 'superadmin']

class IsSuperAdmin(BasePermission):
    """
    Allows access only to superadmin users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'superadmin'

class IsSelfOrAdmin(BasePermission):
    """
    Allows users to access their own data, or admins to access any.
    """
    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated and (
                obj == request.user or
                getattr(obj, 'user', None) == request.user or
                request.user.role in ['admin', 'superadmin']
            )
        )

class IsPatient(BasePermission):
    """
    Allows access only to patient users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'patient'

class IsDoctor(BasePermission):
    """
    Allows access only to doctor users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'doctor'

class IsNurse(BasePermission):
    """
    Allows access only to nurse users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'nurse'

class IsStaff(BasePermission):
    """
    Allows access only to staff users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'staff'