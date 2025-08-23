# queues/throttles.py
from rest_framework.throttling import UserRateThrottle

class QueueJoinThrottle(UserRateThrottle):
    scope = 'queue_join'
    
    def get_rate(self):
        # Different rates based on user role
        user = self.request.user
        if user.role == 'patient':
            return '3/hour'
        elif user.role == 'nurse':
            return '30/minute'
        return '100/hour'  # doctors/admin
