"""
security_middleware.py
Custom middleware for additional security headers.
"""
from django.utils.deprecation import MiddlewareMixin

class CustomSecurityMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=()'
        return response
