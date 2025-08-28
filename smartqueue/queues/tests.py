from django.urls import reverse
from django.test import TestCase
from django.urls import reverse
from .models import Queue, QueueEntry, QueueAnalytics
from users.models import Patient
from hospital.models import Department
from django.contrib.auth import get_user_model

User = get_user_model()

class QueueModelTest(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="General", department_type="OPD", is_active=True)
    def test_create_queue(self):
        queue = Queue.objects.create(name="Main Queue", department=self.dept, is_active=True)
        self.assertEqual(queue.name, "Main Queue")
        self.assertTrue(queue.is_active)

class QueueEntryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="patient1", email="patient1@example.com", password="pass", role="patient")
        self.patient = Patient.objects.create(user=self.user, medical_id="MED00001", priority_level="walk_in")
        self.dept = Department.objects.create(name="General", department_type="OPD", is_active=True)
        self.queue = Queue.objects.create(name="Main Queue", department=self.dept, is_active=True)
    def test_create_queue_entry(self):
        entry = QueueEntry.objects.create(patient=self.patient, queue=self.queue, status="waiting", position=1)
        self.assertEqual(entry.patient.user.username, "patient1")
        self.assertEqual(entry.queue.name, "Main Queue")

class QueueAnalyticsModelTest(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="General", department_type="OPD", is_active=True)
        self.queue = Queue.objects.create(name="Main Queue", department=self.dept, is_active=True)
    def test_create_queue_analytics(self):
        analytics = QueueAnalytics.objects.create(queue=self.queue, date="2025-08-28", total_patients=10)
        self.assertEqual(analytics.queue.name, "Main Queue")
        self.assertEqual(analytics.total_patients, 10)

# Example API test (expand as needed)
from rest_framework.test import APIClient
class QueueAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="admin", email="admin@example.com", password="pass", role="admin")
        # Obtain JWT token if needed, or login
        self.client.force_authenticate(user=self.user)
        self.dept = Department.objects.create(name="General", department_type="OPD", is_active=True)
        self.queue = Queue.objects.create(name="Main Queue", department=self.dept, is_active=True)
    def test_list_queues(self):
        url = reverse('queue_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Main Queue", str(response.content))