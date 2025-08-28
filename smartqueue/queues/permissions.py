from rest_framework import permissions


class CanJoinQueue(permissions.BasePermission):
    """
    Allows only patients to join a queue.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'role', None) == 'patient'


class CanManageQueue(permissions.BasePermission):
    """
    Allows only doctors, nurses, admin, or superadmin to manage queues.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            getattr(request.user, 'role', None) in ['doctor', 'nurse', 'admin', 'superadmin']
        )


class IsQueueOwnerOrReadOnly(permissions.BasePermission):
    """
    Allows queue owners (staff/admin) to edit, others can only read.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Assuming obj has a department and department has staff
        return (
            request.user.is_authenticated and
            hasattr(obj, 'department') and
            obj.department.staff_set.filter(user=request.user).exists()
        )