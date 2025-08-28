from django.utils import timezone
from django.db.models import Avg, Count, Q
from .models import Queue, QueueEntry, QueueAnalytics
from notifications.services import NotificationService
from hospital.models import Department
import datetime

class QueueManagementService:
    def __init__(self):
        self.notification_service = NotificationService()

    def process_no_shows(self):
        """
        Check for no-shows and remove them from queues.
        A no-show is a patient who was called but did not start consultation within 10 minutes.
        """
        no_show_threshold = timezone.now() - timezone.timedelta(minutes=10)
        no_show_entries = QueueEntry.objects.filter(
            status='in_progress',
            called_at__lt=no_show_threshold,
            consultation_start__isnull=True
        )
        for entry in no_show_entries:
            entry.mark_no_show()
            self.notification_service.create_and_send_notification(
                user=entry.patient.user,
                notification_type='queue_update',
                title='Missed Appointment',
                message=f'You missed your appointment at {entry.queue.name}. Please reschedule.',
                channel='sms'
            )

    def send_queue_notifications(self):
        """
        Send notifications to patients about their queue status.
        Notifies patients who are next or second in line.
        """
        upcoming_entries = QueueEntry.objects.filter(
            status='waiting',
            position__lte=2
        ).select_related('patient__user', 'queue')
        for entry in upcoming_entries:
            if entry.position == 1:
                message = f"You're next! Please be ready for {entry.queue.name}."
                title = "You're Next!"
            else:
                message = f"You're #{entry.position} in line for {entry.queue.name}. Estimated wait: {entry.queue.estimated_wait_time} minutes."
                title = "Queue Update"
            self.notification_service.create_and_send_notification(
                user=entry.patient.user,
                notification_type='queue_update',
                title=title,
                message=message,
                channel='sms'
            )

    def handle_emergency_patient(self, patient, queue):
        """
        Insert an emergency patient at the front of the queue and notify others.
        """
        entry = QueueEntry.objects.create(
            patient=patient,
            queue=queue,
            position=1,
            status='waiting'
        )
        # Shift other waiting patients down
        QueueEntry.objects.filter(
            queue=queue,
            status='waiting'
        ).exclude(id=entry.id).update(position=models.F('position') + 1)
        # Notify all waiting patients about the emergency
        waiting_entries = QueueEntry.objects.filter(
            queue=queue,
            status='waiting'
        ).exclude(id=entry.id).select_related('patient__user')
        for waiting_entry in waiting_entries:
            self.notification_service.create_and_send_notification(
                user=waiting_entry.patient.user,
                notification_type='delay_alert',
                title='Emergency Patient Alert',
                message=f'An emergency patient has been added to {queue.name}. Your wait time may be extended.',
                channel='sms'
            )
        return entry

    def optimize_queue_distribution(self, department):
        """
        Distribute patients across multiple queues in a department for load balancing.
        Moves walk-in patients from overcrowded queues to the optimal queue.
        """
        queues = Queue.objects.filter(department=department, is_active=True)
        if not queues.exists():
            return
        optimal_queue = min(queues, key=lambda q: q.estimated_wait_time)
        for queue in queues:
            if queue.current_length > optimal_queue.current_length + 5:
                patients_to_move = QueueEntry.objects.filter(
                    queue=queue,
                    status='waiting',
                    patient__priority_level='walk_in'
                ).order_by('-position')[:2]
                for entry in patients_to_move:
                    entry.queue = optimal_queue
                    entry.position = optimal_queue.current_length + 1
                    entry.save()
                    self.notification_service.create_and_send_notification(
                        user=entry.patient.user,
                        notification_type='queue_update',
                        title='Queue Changed',
                        message=f'You have been moved to {optimal_queue.name} for faster service.',
                        channel='sms'
                    )

    def update_daily_analytics(self):
        """
        Update daily analytics for all active queues.
        Calculates total patients, average wait/processing time, no-shows, and peak hours.
        """
        today = timezone.now().date()
        for queue in Queue.objects.filter(is_active=True):
            completed_entries = QueueEntry.objects.filter(
                queue=queue,
                completed_at__date=today,
                status__in=['completed', 'no_show']
            )
            if not completed_entries.exists():
                continue
            total_patients = completed_entries.count()
            completed_consultations = completed_entries.filter(status='completed')
            avg_wait_time = completed_consultations.aggregate(
                avg=Avg('actual_wait_time')
            )['avg'] or 0
            processing_times = [
                (entry.completed_at - entry.consultation_start).total_seconds() / 60
                for entry in completed_consultations
                if entry.consultation_start and entry.completed_at
            ]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            no_show_count = completed_entries.filter(status='no_show').count()
            hourly_counts = {}
            for entry in completed_entries:
                hour = entry.joined_at.hour
                hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
            if hourly_counts:
                peak_hour = max(hourly_counts, key=hourly_counts.get)
                peak_hour_start = datetime.time(peak_hour, 0)
                peak_hour_end = datetime.time(peak_hour + 1, 0)
            else:
                peak_hour_start = peak_hour_end = None
            analytics, created = QueueAnalytics.objects.get_or_create(
                queue=queue,
                date=today,
                defaults={
                    'total_patients': total_patients,
                    'avg_wait_time': avg_wait_time,
                    'avg_processing_time': avg_processing_time,
                    'no_show_count': no_show_count,
                    'peak_hour_start': peak_hour_start,
                    'peak_hour_end': peak_hour_end,
                }
            )
            if not created:
                analytics.total_patients = total_patients
                analytics.avg_wait_time = avg_wait_time
                analytics.avg_processing_time = avg_processing_time
                analytics.no_show_count = no_show_count
                analytics.peak_hour_start = peak_hour_start
                analytics.peak_hour_end = peak_hour_end
                analytics.save()

    def run_maintenance_tasks(self):
        """
        Run all maintenance tasks: process no-shows, send notifications, update analytics, optimize queues.
        """
        self.process_no_shows()
        self.send_queue_notifications()
        self.update_daily_analytics()
        for department in Department.objects.filter(is_active=True):
            self.optimize_queue_distribution(department)
