from django.db import models


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

class DepartmentStaff(models.Model):
    staff = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, limit_choices_to={'role__in': ['doctor', 'nurse']})
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)
    can_manage_queue = models.BooleanField(default=False)

    class Meta:
        unique_together = ['staff', 'department']
        verbose_name_plural = 'Department Staff'

    def __str__(self):
        return f"{self.staff.username} - {self.department.name}"