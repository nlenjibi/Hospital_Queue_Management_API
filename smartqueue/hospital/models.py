from django.db import models
from users.models import User

class Department(models.Model):
    DEPARTMENT_TYPES = [
        ('OPD', 'Outpatient Department'),
        ('LAB', 'Laboratory'),
        ('PHARMACY', 'Pharmacy'),
        ('ER', 'Emergency Room')
    ]
    name = models.CharField(max_length=100)
    department_type = models.CharField(max_length=20, choices=DEPARTMENT_TYPES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        permissions = [
            ('can_manage_department', 'Can manage department settings')
        ]

    def __str__(self):
        return f"{self.name} ({self.get_department_type_display()})"

class Staff(models.Model):
    SPECIALTY_CHOICES = [
        ('general', 'General Medicine'),
        ('cardiology', 'Cardiology'),
        ('neurology', 'Neurology'),
        ('orthopedics', 'Orthopedics'),
        ('pediatrics', 'Pediatrics'),
        ('emergency', 'Emergency Medicine'),
    ]
    ROLE_CHOICES = [
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('staff', 'Staff'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role__in': ['doctor', 'nurse', 'staff']})
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    specialty = models.CharField(max_length=20, choices=SPECIALTY_CHOICES, blank=True)
    license_number = models.CharField(max_length=50, unique=True, blank=True)
    shift_start = models.TimeField()
    shift_end = models.TimeField()
    is_on_break = models.BooleanField(default=False)
    avg_consultation_time = models.IntegerField(default=15)  # minutes
    is_primary = models.BooleanField(default=False)
    can_manage_queue = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'department']
        verbose_name_plural = 'Staff'

    def __str__(self):
        return f"{self.user.username} ({self.role}) - {self.department.name}"

    @property
    def is_available(self):
        from django.utils import timezone
        current_time = timezone.now().time()
        return (self.shift_start <= current_time <= self.shift_end and 
                not self.is_on_break)