from rest_framework import permissions

class CanSendNotification(permissions.BasePermission):
	"""
	Allows staff, admin, or superadmin to send notifications.
	"""
	def has_permission(self, request, view):
		return (
			request.user.is_authenticated and
			getattr(request.user, 'role', None) in ['staff', 'admin', 'superadmin']
		)

class CanViewNotification(permissions.BasePermission):
	"""
	Allows users to view their own notifications, and staff/admin to view any.
	"""
	def has_object_permission(self, request, view, obj):
		# obj is Notification
		if getattr(request.user, 'role', None) == 'patient':
			return obj.user == request.user
		return getattr(request.user, 'role', None) in ['staff', 'admin', 'superadmin']

class CanManageNotificationPreferences(permissions.BasePermission):
	"""
	Allows users to manage their own notification preferences, and admin/superadmin to manage any.
	"""
	def has_object_permission(self, request, view, obj):
		# obj is NotificationPreference
		if obj.user == request.user:
			return True
		return getattr(request.user, 'role', None) in ['admin', 'superadmin']
