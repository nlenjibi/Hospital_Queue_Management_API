"""
setup_security.py
Script to automate security configuration for Django projects.
"""
import os
import sys

def apply_security_settings(settings_path):
    """Add recommended security settings to Django settings.py."""
    with open(settings_path, 'r') as f:
        content = f.read()
    # Example: Add django-csp to INSTALLED_APPS if not present
    if 'django-csp' not in content:
        content = content.replace(
            "INSTALLED_APPS = [",
            "INSTALLED_APPS = [\n    'django_csp',"
        )
    # Example: Add CSP middleware
    if 'csp.middleware.CSPMiddleware' not in content:
        content = content.replace(
            "MIDDLEWARE = [",
            "MIDDLEWARE = [\n    'csp.middleware.CSPMiddleware',"
        )
    with open(settings_path, 'w') as f:
        f.write(content)
    print("Security settings applied.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python setup_security.py <settings.py path>")
        sys.exit(1)
    apply_security_settings(sys.argv[1])
