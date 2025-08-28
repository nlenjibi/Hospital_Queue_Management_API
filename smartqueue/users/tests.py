from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from .models import User, Patient

class UserModelTest(TestCase):
	def test_create_user(self):
		user = User.objects.create_user(username="johndoe", email="john@example.com", password="pass", role="patient")
		self.assertEqual(user.username, "johndoe")
		self.assertEqual(user.email, "john@example.com")
		self.assertEqual(user.role, "patient")

class PatientModelTest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="janedoe", email="jane@example.com", password="pass", role="patient")
	def test_create_patient(self):
		patient = Patient.objects.create(user=self.user, medical_id="MED12345", priority_level="walk_in")
		self.assertEqual(patient.user.username, "janedoe")
		self.assertEqual(patient.medical_id, "MED12345")
		self.assertEqual(patient.priority_level, "walk_in")

class UserAPITest(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.admin = User.objects.create_user(username="admin", email="admin@example.com", password="pass", role="admin")
		# Obtain JWT token
		response = self.client.post(reverse('login'), {"email": "admin@example.com", "password": "pass"}, format='json')
		self.token = response.data.get('access')
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

	def test_list_users(self):
		url = reverse('user_list')
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertIn("admin@example.com", str(response.content))

	def test_create_user_api(self):
		url = reverse('register')
		data = {
			"username": "newuser",
			"email": "newuser@example.com",
			"password": "newpass123",
			"password_confirm": "newpass123",
			"role": "patient"
		}
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, 201)
		self.assertIn("newuser@example.com", str(response.content))

	def test_patient_profile_api(self):
		# Register a patient and login
		reg_url = reverse('register')
		data = {
			"username": "pat",
			"email": "pat@example.com",
			"password": "patpass123",
			"password_confirm": "patpass123",
			"role": "patient"
		}
		self.client.credentials()  # Clear any existing authentication
		reg_resp = self.client.post(reg_url, data, format='json')
		self.assertEqual(reg_resp.status_code, 201)
		token = reg_resp.data['access']
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
		profile_url = reverse('patient_profile')
		resp = self.client.get(profile_url)
		self.assertEqual(resp.status_code, 200)
		self.assertIn("pat@example.com", str(resp.content))
