# queues/throttles.py
from rest_framework.throttling import UserRateThrottle

class QueueJoinThrottle(UserRateThrottle):
    """
    Custom throttle for joining queues.
    Limits requests based on user role to prevent abuse.
    """
    scope = 'queue_join'

    def get_rate(self):
        user = getattr(self.request, 'user', None)
        # Patients have lowest rate, nurses moderate, doctors/admin highest
        if user and user.is_authenticated:
            if user.role == 'patient':
                return '10/hour'
            elif user.role == 'nurse':
                return '30/minute'
            elif user.role in ['doctor', 'admin', 'superadmin']:
                return '100/hour'
        # Unauthenticated or unknown role: very limited
