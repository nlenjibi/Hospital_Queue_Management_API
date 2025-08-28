from django.db import models
from django.utils import timezone
from users.models import Patient
from hospital.models import Staff, Department
from queues.models import QueueEntry

class LabDepartment(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    operating_hours_start = models.TimeField(default='08:00')
    operating_hours_end = models.TimeField(default='18:00')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @property
    def is_open(self):
        current_time = timezone.now().time()
        return self.operating_hours_start <= current_time <= self.operating_hours_end

class LabTechnician(models.Model):
    SPECIALIZATION_CHOICES = [
        ('hematology', 'Hematology'),
        ('chemistry', 'Clinical Chemistry'),
        ('microbiology', 'Microbiology'),
        ('pathology', 'Pathology'),
        ('radiology', 'Radiology'),
        ('cardiology', 'Cardiology'),
        ('general', 'General Lab'),
    ]
    staff = models.OneToOneField(Staff, on_delete=models.CASCADE)
    lab_department = models.ForeignKey(LabDepartment, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=20, choices=SPECIALIZATION_CHOICES)
    license_number = models.CharField(max_length=50, unique=True)
    certification_expiry = models.DateField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.specialization}"

class LabEquipment(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('in_use', 'In Use'),
        ('maintenance', 'Under Maintenance'),
        ('out_of_order', 'Out of Order'),
    ]
    name = models.CharField(max_length=100)
    model = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, unique=True)
    lab_department = models.ForeignKey(LabDepartment, on_delete=models.CASCADE)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    last_maintenance = models.DateTimeField(null=True, blank=True)
    next_maintenance = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.serial_number}"

class LabTest(models.Model):
    TEST_TYPE_CHOICES = [
        ('blood_count', 'Complete Blood Count'),
        ('blood_chemistry', 'Blood Chemistry Panel'),
        ('urine_analysis', 'Urine Analysis'),
        ('lipid_panel', 'Lipid Panel'),
        ('liver_function', 'Liver Function Test'),
        ('kidney_function', 'Kidney Function Test'),
        ('thyroid_function', 'Thyroid Function Test'),
        ('glucose_test', 'Glucose Test'),
        ('hba1c', 'HbA1c Test'),
        ('xray_chest', 'Chest X-Ray'),
        ('xray_bone', 'Bone X-Ray'),
        ('ct_scan', 'CT Scan'),
        ('mri_scan', 'MRI Scan'),
        ('ultrasound', 'Ultrasound'),
        ('ecg', 'ECG'),
        ('echo', 'Echocardiogram'),
        ('culture', 'Culture Test'),
        ('biopsy', 'Biopsy'),
    ]
    
    STATUS_CHOICES = [
        ('ordered', 'Ordered'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
        ('reported', 'Reported'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('stat', 'STAT'),
    ]
    
    # Basic Information
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    test_type = models.CharField(max_length=20, choices=TEST_TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='routine')
    
    # Ordering Information
    ordered_by = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='ordered_tests')
    ordered_at = models.DateTimeField(auto_now_add=True)
    clinical_notes = models.TextField(blank=True)
    
    # Lab Assignment
    lab_department = models.ForeignKey(LabDepartment, on_delete=models.CASCADE)
    assigned_technician = models.ForeignKey(LabTechnician, on_delete=models.SET_NULL, null=True, blank=True)
    equipment_used = models.ForeignKey(LabEquipment, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    estimated_duration = models.IntegerField(default=30)  # minutes
    
    # Workflow Status
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ordered')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reported_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    results = models.TextField(blank=True)
    normal_ranges = models.JSONField(default=dict, blank=True)
    abnormal_flags = models.JSONField(default=list, blank=True)
    reviewed_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_tests')
    
    # Queue Integration
    original_queue_entry = models.ForeignKey(QueueEntry, on_delete=models.SET_NULL, null=True, blank=True)
    queue_reentry = models.BooleanField(default=True)
    queue_reentry_priority = models.CharField(max_length=15, default='appointment')
    
    # File Attachments
    result_file = models.FileField(upload_to='lab_results/', null=True, blank=True)
    
    class Meta:
        ordering = ['-ordered_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['lab_department']),
        ]

    def __str__(self):
        return f"{self.patient.user.get_full_name()} - {self.get_test_type_display()}"
    
    def save(self, *args, **kwargs):
        # Auto-assign lab department based on test type
        if not self.lab_department_id:
            self.lab_department = self.get_appropriate_lab_department()
        # Ensure assigned technician is available
        if self.assigned_technician and not self.assigned_technician.is_available:
            raise ValueError("Assigned technician is not available.")
        super().save(*args, **kwargs)
    
    def get_appropriate_lab_department(self):
        """Auto-assign lab department based on test type"""
        test_to_dept_mapping = {
            'blood_count': 'hematology',
            'blood_chemistry': 'chemistry',
            'urine_analysis': 'chemistry',
            'culture': 'microbiology',
            'biopsy': 'pathology',
            'xray_chest': 'radiology',
            'xray_bone': 'radiology',
            'ct_scan': 'radiology',
            'mri_scan': 'radiology',
            'ultrasound': 'radiology',
            'ecg': 'cardiology',
            'echo': 'cardiology',
        }
        
        dept_name = test_to_dept_mapping.get(self.test_type, 'general')
        
        try:
            return LabDepartment.objects.get(name__icontains=dept_name, is_active=True)
        except LabDepartment.DoesNotExist:
            return LabDepartment.objects.filter(is_active=True).first()
    
    def start_test(self, technician=None, equipment=None):
        """Start the lab test"""
        self.status = 'in_progress'
        self.started_at = timezone.now()
        
        if technician:
            self.assigned_technician = technician
        if equipment:
            self.equipment_used = equipment
            equipment.status = 'in_use'
            equipment.save()
        
        self.save()
    
    def complete_test(self, results='', normal_ranges=None, abnormal_flags=None):
        """Complete the lab test"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.results = results
        
        if normal_ranges:
            self.normal_ranges = normal_ranges
        if abnormal_flags:
            self.abnormal_flags = abnormal_flags
        
        # Free up equipment
        if self.equipment_used:
            self.equipment_used.status = 'available'
            self.equipment_used.save()
        
        self.save()
        
        # Handle queue reentry
        if self.queue_reentry and self.original_queue_entry:
            self.handle_queue_reentry()
    
    def review_test(self, reviewer, approved=True):
        """Review and approve test results"""
        self.status = 'reviewed'
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewer
        self.save()
        
        if approved:
            self.report_results()
    
    def report_results(self):
        """Report results to patient and ordering physician"""
        self.status = 'reported'
        self.reported_at = timezone.now()
        self.save()
        
        # Send notifications
        from notifications.services import NotificationService
        notification_service = NotificationService()
        
        # Notify patient
        notification_service.send_lab_results_ready(self)
        
        # Notify ordering physician
        notification_service.create_and_send_notification(
            user=self.ordered_by.user,
            notification_type='test_ready',
            title=f'Lab Results Ready - {self.patient.user.get_full_name()}',
            message=f'{self.get_test_type_display()} results are ready for {self.patient.user.get_full_name()}.',
            channel='email'
        )
    
    def handle_queue_reentry(self):
        """Handle patient returning to queue after lab test"""
        if not self.original_queue_entry:
            return
        
        # Return patient to original queue with priority
        self.original_queue_entry.return_from_lab()
        
        # Send notification
        from notifications.services import NotificationService
        notification_service = NotificationService()
        
        notification_service.create_and_send_notification(
            user=self.patient.user,
            notification_type='queue_update',
            title='Returned to Queue',
            message=f'Your lab test is complete. You have been returned to {self.original_queue_entry.queue.name}.',
            channel='sms'
        )
    
    @property
    def estimated_completion_time(self):
        """Calculate estimated completion time"""
        if self.scheduled_at:
            return self.scheduled_at + timezone.timedelta(minutes=self.estimated_duration)
        return None
    
    @property
    def is_overdue(self):
        """Check if test is overdue"""
        if self.status in ['completed', 'reviewed', 'reported', 'cancelled']:
            return False
        
        if self.priority == 'stat':
            # STAT tests should be completed within 1 hour
            deadline = self.ordered_at + timezone.timedelta(hours=1)
        elif self.priority == 'urgent':
            # Urgent tests should be completed within 4 hours
            deadline = self.ordered_at + timezone.timedelta(hours=4)
        else:
            # Routine tests should be completed within 24 hours
            deadline = self.ordered_at + timezone.timedelta(hours=24)
        
        return timezone.now() > deadline

class LabTestTemplate(models.Model):
    """Template for common lab test configurations"""
    name = models.CharField(max_length=100)
    test_type = models.CharField(max_length=20, choices=LabTest.TEST_TYPE_CHOICES)
    lab_department = models.ForeignKey(LabDepartment, on_delete=models.CASCADE)
    estimated_duration = models.IntegerField(default=30)
    normal_ranges = models.JSONField(default=dict)
    instructions = models.TextField(blank=True)
    preparation_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['name', 'test_type', 'lab_department']

    def __str__(self):
        return self.name

class LabSchedule(models.Model):
    """Lab scheduling for tests requiring appointments"""
    lab_test = models.OneToOneField(LabTest, on_delete=models.CASCADE)
    technician = models.ForeignKey(LabTechnician, on_delete=models.CASCADE)
    equipment = models.ForeignKey(LabEquipment, on_delete=models.SET_NULL, null=True, blank=True)
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    duration_minutes = models.IntegerField(default=30)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['technician', 'scheduled_date', 'scheduled_time']
        indexes = [
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['technician']),
        ]

class LabAnalytics(models.Model):
    """Daily analytics for lab departments"""
    lab_department = models.ForeignKey(LabDepartment, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    
    # Test counts
    total_tests_ordered = models.IntegerField(default=0)
    tests_completed = models.IntegerField(default=0)
    tests_pending = models.IntegerField(default=0)
    tests_overdue = models.IntegerField(default=0)
    
    # Performance metrics
    avg_turnaround_time = models.FloatField(default=0.0)  # hours
    avg_processing_time = models.FloatField(default=0.0)  # minutes
    
    # Priority breakdown
    stat_tests = models.IntegerField(default=0)
    urgent_tests = models.IntegerField(default=0)
    routine_tests = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['lab_department', 'date']
        indexes = [
            models.Index(fields=['lab_department', 'date']),
        ]
    
    def __str__(self):
        return f"{self.lab_department.name} - {self.date}"
