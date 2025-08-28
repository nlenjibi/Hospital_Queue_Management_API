from django.test import TestCase
from django.urls import reverse
from .models import LabDepartment, LabTest
from users.models import Patient
from hospital.models import Staff
from django.contrib.auth import get_user_model

User = get_user_model()

class LabDepartmentModelTest(TestCase):
	def test_create_lab_department(self):
		dept = LabDepartment.objects.create(name="Hematology", is_active=True)
		self.assertEqual(dept.name, "Hematology")
		self.assertTrue(dept.is_active)

class LabTestModelTest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="patient1", password="pass", role="patient")
		self.patient = Patient.objects.create(user=self.user)
		self.staff_user = User.objects.create_user(username="staff1", password="pass", role="staff")
		self.staff = Staff.objects.create(user=self.staff_user, role="staff", department=None, shift_start="08:00", shift_end="16:00")
		self.dept = LabDepartment.objects.create(name="Chemistry", is_active=True)

	def test_create_lab_test(self):
		test = LabTest.objects.create(
			patient=self.patient,
			test_type="blood_chemistry",
			priority="routine",
			ordered_by=self.staff,
			lab_department=self.dept
		)
		self.assertEqual(test.test_type, "blood_chemistry")
		self.assertEqual(test.patient.user.username, "patient1")

# Example API test (expand as needed)
class LabDepartmentAPITest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="admin", password="pass", role="admin")
		self.client.login(username="admin", password="pass")
		self.dept = LabDepartment.objects.create(name="Microbiology", is_active=True)

	def test_list_lab_departments(self):
		url = reverse('labdepartment-list')
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertIn("Microbiology", str(response.content))
