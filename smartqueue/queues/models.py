
from django.db import models
from django.utils import timezone

class PatientQueue(models.Model):
    department = models.ForeignKey('departments.Department', on_delete=models.CASCADE)
    current_position = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    max_capacity = models.IntegerField(default=50)
    estimated_wait_time = models.IntegerField(default=15)  # minutes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['department__name']
        permissions = [
            ('can_manage_queue', 'Can manage queue operations')
        ]

    def __str__(self):
        return f"{self.department.name} Queue"

    def get_active_count(self):
        return self.queue_entries.filter(status__in=['waiting', 'processing']).count()

class QueueEntry(models.Model):
    PRIORITY_LEVELS = [
        (0, 'Emergency'),
        (1, 'Urgent'),
        (2, 'Standard'),
        (3, 'Low')
    ]
    
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    queue = models.ForeignKey(PatientQueue, on_delete=models.CASCADE, related_name='queue_entries')
    patient = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, limit_choices_to={'role': 'patient'})
    priority = models.IntegerField(choices=PRIORITY_LEVELS, default=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    position = models.IntegerField()
    joined_at = models.DateTimeField(default=timezone.now)
    called_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['priority', 'joined_at']
        unique_together = ['queue', 'patient', 'status']
        indexes = [
            models.Index(fields=['queue', 'status']),
            models.Index(fields=['priority', 'joined_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.position:
            last_position = QueueEntry.objects.filter(
                queue=self.queue, 
                status__in=['waiting', 'processing']
            ).aggregate(models.Max('position'))['position__max'] or 0
            self.position = last_position + 1
        super().save(*args, **kwargs)

    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    def get_priority_display(self):
        return dict(self.PRIORITY_LEVELS).get(self.priority, self.priority)
    def __str__(self):
        return f"{self.patient.username} - Position {self.position}"