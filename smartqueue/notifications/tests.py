from django.test import TestCase
from django.urls import reverse
from .models import Notification, NotificationPreference
from users.models import User

class NotificationModelTest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="patient1", password="pass", role="patient")

	def test_create_notification(self):
		notif = Notification.objects.create(
			user=self.user,
			type="queue_update",
			channel="sms",
			title="Queue Update",
			message="You are now number 2 in the queue."
		)
		self.assertEqual(notif.type, "queue_update")
		self.assertEqual(notif.user.username, "patient1")

class NotificationPreferenceModelTest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="patient2", password="pass", role="patient")

	def test_create_preference(self):
		pref = NotificationPreference.objects.create(
			user=self.user,
			queue_updates="sms",
			appointment_reminders="email",
			delay_alerts="sms",
			test_results="email"
		)
		self.assertEqual(pref.user.username, "patient2")
		self.assertEqual(pref.queue_updates, "sms")

# Example API test (expand as needed)
class NotificationAPITest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="admin", password="pass", role="admin")
		self.client.login(username="admin", password="pass")
		Notification.objects.create(
			user=self.user,
			type="queue_update",
			channel="sms",
			title="Queue Update",
			message="You are now number 2 in the queue."
		)

	def test_list_notifications(self):
		url = reverse('notification-list')
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertIn("Queue Update", str(response.content))
