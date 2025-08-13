"""
Custom Security Middleware for Hospital Queue Management API

Adds enhanced security headers and logs suspicious requests.
"""

import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger('django.security')

class SecurityMiddleware(MiddlewareMixin):
    """
    Adds security headers and logs suspicious activity.
    """

    def process_request(self, request):
        # Log suspicious user agents
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        suspicious_agents = ['sqlmap', 'nikto', 'dirb', 'nmap']
        if any(agent in user_agent.lower() for agent in suspicious_agents):
            logger.warning(f"Suspicious user agent: {user_agent} from {self.get_client_ip(request)}")

        # Log suspicious URL patterns
        suspicious_patterns = ['../../../', 'union+select', '<script>', 'javascript:', 'eval(']
        request_path = request.get_full_path().lower()
        for pattern in suspicious_patterns:
            if pattern in request_path:
                logger.warning(f"Suspicious URL pattern '{pattern}' from {self.get_client_ip(request)}: {request_path}")

        return None

   

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
