from django.db import models
from django.utils import timezone
from django.db.models import Avg
from hospital.models import Department
from users.models import Patient

class Queue(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='queues')
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    max_capacity = models.IntegerField(default=50)
    avg_processing_time = models.IntegerField(default=15)  # minutes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['department__name', 'name']
        permissions = [
            ('can_manage_queue', 'Can manage queue operations')
        ]

    def __str__(self):
        return f"{self.department.name} - {self.name}"

    @property
    def current_length(self):
        # Count patients currently waiting in the queue
        return self.queueentry_set.filter(status='waiting').count()

    @property
    def estimated_wait_time(self):
        """
        Estimate wait time for the queue based on staff availability and patient priority.
        """
        waiting_entries = self.queueentry_set.filter(status='waiting').order_by('position')
        if not waiting_entries.exists():
            return 0

        # Get available staff for this department
        available_staff = self.department.staff_set.filter(
            is_on_break=False,
            shift_start__lte=timezone.now().time(),
            shift_end__gte=timezone.now().time()
        )
        if not available_staff.exists():
            return 999  # No staff available

        staff_avg_time = available_staff.aggregate(
            avg_time=Avg('avg_consultation_time')
        )['avg_time'] or self.avg_processing_time

        priority_weights = {'emergency': 0.7, 'appointment': 1.0, 'walk_in': 1.2}
        total_estimated_time = 0
        staff_count = available_staff.count()

        for i, entry in enumerate(waiting_entries):
            priority_weight = priority_weights.get(entry.patient.priority_level, 1.0)
            processing_time = staff_avg_time * priority_weight
            queue_position_factor = (i // staff_count) + 1
            total_estimated_time += processing_time * queue_position_factor

        return int(total_estimated_time / staff_count)

    def reorder_queue(self):
        """
        Reorder queue entries by priority: Emergency > Appointment > Walk-in.
        """
        entries = list(self.queueentry_set.filter(status='waiting').order_by('joined_at'))
        emergency_entries = [e for e in entries if e.patient.priority_level == 'emergency']
        appointment_entries = [e for e in entries if e.patient.priority_level == 'appointment']
        walk_in_entries = [e for e in entries if e.patient.priority_level == 'walk_in']
        reordered_entries = emergency_entries + appointment_entries + walk_in_entries
        for i, entry in enumerate(reordered_entries, 1):
            entry.position = i
            entry.save(update_fields=['position'])

    def get_next_patient(self):
        """
        Get the next patient to be called from the queue.
        """
        return self.queueentry_set.filter(status='waiting').order_by('position').first()

class QueueEntry(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('in_test', 'In Test'),
        ('no_show', 'No Show'),
        ('cancelled', 'Cancelled'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='waiting')
    position = models.IntegerField()
    joined_at = models.DateTimeField(auto_now_add=True)
    called_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    estimated_time = models.DateTimeField(null=True, blank=True)
    no_show_check_time = models.DateTimeField(null=True, blank=True)
    actual_wait_time = models.IntegerField(null=True, blank=True)  # minutes
    consultation_start = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['patient', 'queue']
        ordering = ['position']

    def __str__(self):
        return f"{self.patient.user.get_full_name()} in {self.queue.name}"

    def save(self, *args, **kwargs):
        # Assign position if not set
        if not self.position:
            self.assign_position()
        # Update estimated time if waiting
        if self.status == 'waiting':
            self.update_estimated_time()
        super().save(*args, **kwargs)

    def assign_position(self):
        """
        Assign position in queue based on patient priority.
        Emergency patients go to the front, others to the end.
        """
        priority_order = {'emergency': 1, 'appointment': 2, 'walk_in': 3}
        patient_priority = priority_order.get(self.patient.priority_level, 3)
        if self.patient.priority_level == 'emergency':
            self.position = 1
            # Shift other patients down
            QueueEntry.objects.filter(
                queue=self.queue,
                status='waiting'
            ).update(position=models.F('position') + 1)
        else:
            last_position = QueueEntry.objects.filter(
                queue=self.queue,
                status='waiting'
            ).aggregate(models.Max('position'))['position__max'] or 0
            self.position = last_position + 1

    def update_estimated_time(self):
        """
        Update estimated call time based on queue state and position.
        """
        if self.status != 'waiting':
            return
        queue_wait_time = self.queue.estimated_wait_time
        position_factor = max(1, self.position - 1)
        estimated_minutes = (queue_wait_time * position_factor) / max(1, self.queue.current_length)
        self.estimated_time = timezone.now() + timezone.timedelta(minutes=estimated_minutes)

    def mark_no_show(self):
        """
        Mark patient as no-show and remove from queue.
        """
        self.status = 'no_show'
        self.completed_at = timezone.now()
        self.save()
        # Shift remaining patients up
        QueueEntry.objects.filter(
            queue=self.queue,
            status='waiting',
            position__gt=self.position
        ).update(position=models.F('position') - 1)

    def call_patient(self):
        """
        Mark patient as called and in progress.
        """
        self.status = 'in_progress'
        self.called_at = timezone.now()
        self.consultation_start = timezone.now()
        # Calculate actual wait time
        if self.joined_at:
            wait_delta = timezone.now() - self.joined_at
            self.actual_wait_time = int(wait_delta.total_seconds() / 60)
        self.save()

    def complete_consultation(self):
        """
        Mark consultation as completed.
        """
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def send_to_lab(self):
        """
        Send patient to lab and pause in queue.
        """
        self.status = 'in_test'
        self.save()

    def return_from_lab(self):
        """
        Return patient from lab and resume in queue (usually at front).
        """
        self.status = 'waiting'
        self.position = 1
        QueueEntry.objects.filter(
            queue=self.queue,
            status='waiting'
        ).exclude(id=self.id).update(position=models.F('position') + 1)
        self.save()

class QueueAnalytics(models.Model):
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    total_patients = models.IntegerField(default=0)
    avg_wait_time = models.FloatField(default=0.0)
    avg_processing_time = models.FloatField(default=0.0)
    no_show_count = models.IntegerField(default=0)
    peak_hour_start = models.TimeField(null=True, blank=True)
    peak_hour_end = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = ['queue', 'date']

    def __str__(self):
        return f"{self.queue.name} - {self.date}"