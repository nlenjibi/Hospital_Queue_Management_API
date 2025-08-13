"""
test_security.py
Basic tests for security settings in Django settings.py.
"""
import unittest

class TestSecuritySettings(unittest.TestCase):
    def test_csp_installed(self):
        with open('smartqueue/smartqueue/settings.py') as f:
            content = f.read()
        self.assertIn('django_csp', content)

    def test_csp_middleware(self):
        with open('smartqueue/smartqueue/settings.py') as f:
            content = f.read()
        self.assertIn('csp.middleware.CSPMiddleware', content)

    def test_security_headers(self):
        with open('smartqueue/smartqueue/settings.py') as f:
            content = f.read()
        self.assertIn('SECURE_BROWSER_XSS_FILTER = True', content)
        self.assertIn('SECURE_CONTENT_TYPE_NOSNIFF = True', content)
        self.assertIn("X_FRAME_OPTIONS = 'DENY'", content)

if __name__ == "__main__":
    unittest.main()
