from django.test import TestCase
from django.urls import reverse
from .models import Department, Staff
from django.contrib.auth import get_user_model

User = get_user_model()

class DepartmentModelTest(TestCase):
	def test_create_department(self):
		dept = Department.objects.create(name="Cardiology", is_active=True)
		self.assertEqual(dept.name, "Cardiology")
		self.assertTrue(dept.is_active)

	# Removed invalid Staff creation (no email, wrong fields)

class StaffModelTest(TestCase):
	def setUp(self):
		from users.models import User
		self.user = User.objects.create_user(username="drsmith", email="drsmith@example.com", password="pass", role="doctor")
		self.dept = Department.objects.create(name="Cardiology", department_type="OPD", is_active=True)
	def test_create_staff(self):
		staff = Staff.objects.create(
			user=self.user,
			department=self.dept,
			role="doctor",
			specialty="cardiology",
			license_number="LIC12345",
			shift_start="08:00",
			shift_end="16:00"
		)
		self.assertEqual(staff.user.username, "drsmith")
		self.assertEqual(staff.role, "doctor")
		self.assertEqual(staff.department.name, "Cardiology")

	# Removed duplicate/invalid setUp and tests
class DepartmentAPITest(TestCase):
from rest_framework.test import APIClient
class DepartmentAPITest(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(username="admin", email="admin@example.com", password="pass", role="admin")
		# Obtain JWT token
		login_url = reverse('login')
		response = self.client.post(login_url, {"email": "admin@example.com", "password": "pass"}, format='json')
		token = response.data.get('access')
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
		self.dept = Department.objects.create(name="Radiology", department_type="OPD", is_active=True)

	def test_list_departments(self):
		url = reverse('department_list')
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertIn("Radiology", str(response.content))

	def test_department_detail(self):
		url = reverse('department_detail', args=[self.dept.id])
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertIn("Radiology", str(response.content))

class StaffAPITest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="admin", email="admin@example.com", password="pass", role="admin")
		self.client.login(username="admin", password="pass")
		# Fix Staff creation to use correct fields
		self.staff_user = User.objects.create_user(username="drjane", email="drjane@example.com", password="pass", role="doctor")
		self.dept = Department.objects.create(name="Cardiology", department_type="OPD", is_active=True)
		self.staff = Staff.objects.create(
			user=self.staff_user,
			department=self.dept,
			role="doctor",
			specialty="cardiology",
			license_number="LIC67890",
			shift_start="08:00",
			shift_end="16:00"
		)

	def test_list_staff(self):
		url = reverse('staff_list')
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertIn("drjane", str(response.content))

	def test_staff_detail(self):
		url = reverse('staff_detail', args=[self.staff.id])
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertIn("drjane", str(response.content))
from django.test import TestCase

# Create your tests here.
