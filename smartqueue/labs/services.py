from django.utils import timezone
from django.db.models import Count, Avg, Q
from .models import LabTest, LabDepartment, LabTechnician, LabEquipment, LabSchedule, LabAnalytics
from queues.models import QueueEntry
from notifications.services import NotificationService
import datetime

class LabManagementService:
    def __init__(self):
        self.notification_service = NotificationService()
    
    def order_lab_test(self, patient, test_type, ordered_by, priority='routine', clinical_notes='', queue_entry=None):
        """Order a new lab test and handle queue integration"""
        lab_test = LabTest.objects.create(
            patient=patient,
            test_type=test_type,
            priority=priority,
            ordered_by=ordered_by,
            clinical_notes=clinical_notes,
            original_queue_entry=queue_entry
        )
        
        # If patient is currently in queue, send them to lab
        if queue_entry:
            queue_entry.send_to_lab()
            
            # Notify patient about lab test
            self.notification_service.create_and_send_notification(
                user=patient.user,
                notification_type='test_ready',
                title='Lab Test Ordered',
                message=f'You have been sent for {lab_test.get_test_type_display()}. Please proceed to {lab_test.lab_department.name}.',
                channel='sms'
            )
        
        # Auto-schedule if possible
        self.auto_schedule_test(lab_test)
        
        return lab_test
    
    def auto_schedule_test(self, lab_test):
        """Automatically schedule lab test based on priority and availability"""
        if lab_test.priority == 'stat':
            # STAT tests are done immediately
            available_tech = self.find_available_technician(lab_test.lab_department, lab_test.test_type)
            if available_tech:
                lab_test.assigned_technician = available_tech
                lab_test.scheduled_at = timezone.now()
                lab_test.status = 'scheduled'
                lab_test.save()
                return True
        
        elif lab_test.priority == 'urgent':
            # Urgent tests scheduled within 2 hours
            target_time = timezone.now() + timezone.timedelta(hours=2)
            return self.schedule_test(lab_test, target_time)
        
        else:
            # Routine tests scheduled for next available slot
            target_time = timezone.now() + timezone.timedelta(hours=4)
            return self.schedule_test(lab_test, target_time)
        
        return False
    
    def schedule_test(self, lab_test, preferred_time):
        """Schedule a lab test for a specific time"""
        technician = self.find_available_technician(
            lab_test.lab_department, 
            lab_test.test_type, 
            preferred_time
        )
        if not technician:
            # Optionally notify staff/admin about lack of technician
            self.notification_service.create_and_send_notification(
                user=lab_test.ordered_by.user,
                notification_type='schedule_error',
                title='No Technician Available',
                message=f'No technician available for {lab_test.get_test_type_display()} at {preferred_time}.',
                channel='email'
            )
            return False

        equipment = self.find_available_equipment(
            lab_test.lab_department,
            lab_test.test_type,
            preferred_time
        )
        if not equipment:
            self.notification_service.create_and_send_notification(
                user=lab_test.ordered_by.user,
                notification_type='schedule_error',
                title='No Equipment Available',
                message=f'No equipment available for {lab_test.get_test_type_display()} at {preferred_time}.',
                channel='email'
            )
            return False

        # Create schedule
        schedule = LabSchedule.objects.create(
            lab_test=lab_test,
            technician=technician,
            equipment=equipment,
            scheduled_date=preferred_time.date(),
            scheduled_time=preferred_time.time(),
            duration_minutes=lab_test.estimated_duration
        )
        
        lab_test.scheduled_at = preferred_time
        lab_test.assigned_technician = technician
        lab_test.equipment_used = equipment
        lab_test.status = 'scheduled'
        lab_test.save()
        
        # Send notification
        self.notification_service.create_and_send_notification(
            user=lab_test.patient.user,
            notification_type='appointment_reminder',
            title='Lab Test Scheduled',
            message=f'Your {lab_test.get_test_type_display()} is scheduled for {preferred_time.strftime("%Y-%m-%d %H:%M")} at {lab_test.lab_department.name}.',
            channel='sms'
        )
        
        return True
    
    def find_available_technician(self, lab_department, test_type, target_time=None):
        """Find available technician for a specific test type"""
        # Map test types to specializations
        specialization_mapping = {
            'blood_count': 'hematology',
            'blood_chemistry': 'chemistry',
            'urine_analysis': 'chemistry',
            'culture': 'microbiology',
            'biopsy': 'pathology',
            'xray_chest': 'radiology',
            'ct_scan': 'radiology',
            'mri_scan': 'radiology',
            'ecg': 'cardiology',
        }
        
        preferred_specialization = specialization_mapping.get(test_type, 'general')
        
        # Find technicians with matching specialization
        technicians = LabTechnician.objects.filter(
            lab_department=lab_department,
            specialization__in=[preferred_specialization, 'general'],
            is_available=True
        )
        
        if target_time:
            # Check availability at specific time
            for tech in technicians:
                if self.is_technician_available(tech, target_time):
                    return tech
        else:
            # Return first available technician
            return technicians.first()
        
        return None
    
    def find_available_equipment(self, lab_department, test_type, target_time=None):
        """Find available equipment for a specific test type"""
        # Map test types to equipment requirements
        equipment_mapping = {
            'blood_count': 'hematology_analyzer',
            'blood_chemistry': 'chemistry_analyzer',
            'xray_chest': 'xray_machine',
            'ct_scan': 'ct_scanner',
            'mri_scan': 'mri_machine',
            'ecg': 'ecg_machine',
        }
        
        equipment_type = equipment_mapping.get(test_type)
        if not equipment_type:
            return None
        
        equipment = LabEquipment.objects.filter(
            lab_department=lab_department,
            name__icontains=equipment_type,
            status='available'
        )
        
        if target_time:
            # Check equipment availability at specific time
            for eq in equipment:
                if self.is_equipment_available(eq, target_time):
                    return eq
        else:
            return equipment.first()
        
        return None
    
    def is_technician_available(self, technician, target_time):
        """Check if technician is available at specific time"""
        # Check for existing schedules
        existing_schedules = LabSchedule.objects.filter(
            technician=technician,
            scheduled_date=target_time.date(),
            scheduled_time__range=[
                (target_time - timezone.timedelta(hours=1)).time(),
                (target_time + timezone.timedelta(hours=1)).time()
            ]
        )
        
        return not existing_schedules.exists()
    
    def is_equipment_available(self, equipment, target_time):
        """Check if equipment is available at specific time"""
        # Check for existing schedules
        existing_schedules = LabSchedule.objects.filter(
            equipment=equipment,
            scheduled_date=target_time.date(),
            scheduled_time__range=[
                (target_time - timezone.timedelta(hours=1)).time(),
                (target_time + timezone.timedelta(hours=1)).time()
            ]
        )
        
        return not existing_schedules.exists()
    
    def process_overdue_tests(self):
        """Process overdue lab tests and send alerts"""
        overdue_tests = LabTest.objects.filter(
            status__in=['ordered', 'scheduled', 'in_progress']
        )
        
        for test in overdue_tests:
            if test.is_overdue:
                # Send alert to lab department
                self.notification_service.create_and_send_notification(
                    user=test.assigned_technician.staff.user if test.assigned_technician else test.ordered_by.user,
                    notification_type='delay_alert',
                    title='Overdue Lab Test',
                    message=f'Lab test {test.get_test_type_display()} for {test.patient.user.get_full_name()} is overdue.',
                    channel='email'
                )
                
                # Send update to patient
                self.notification_service.create_and_send_notification(
                    user=test.patient.user,
                    notification_type='delay_alert',
                    title='Lab Test Delay',
                    message=f'Your {test.get_test_type_display()} is taking longer than expected. We will update you soon.',
                    channel='sms'
                )
    
    def complete_test_workflow(self, lab_test, results, normal_ranges=None, abnormal_flags=None):
        """Complete the full test workflow including review and reporting"""
        # Complete the test
        lab_test.complete_test(results, normal_ranges, abnormal_flags)
        
        # Auto-review routine tests with normal results
        if lab_test.priority == 'routine' and not abnormal_flags:
            lab_test.review_test(lab_test.ordered_by, approved=True)
        else:
            # Send for manual review
            self.notification_service.create_and_send_notification(
                user=lab_test.ordered_by.user,
                notification_type='test_ready',
                title='Lab Test Ready for Review',
                message=f'{lab_test.get_test_type_display()} for {lab_test.patient.user.get_full_name()} requires review.',
                channel='email'
            )
    
    def update_daily_analytics(self):
        """Update daily analytics for all lab departments"""
        today = timezone.now().date()
        
        for lab_dept in LabDepartment.objects.filter(is_active=True):
            # Get today's tests
            today_tests = LabTest.objects.filter(
                lab_department=lab_dept,
                ordered_at__date=today
            )
            
            if not today_tests.exists():
                continue
            
            # Calculate metrics
            total_ordered = today_tests.count()
            completed = today_tests.filter(status__in=['completed', 'reviewed', 'reported']).count()
            pending = today_tests.filter(status__in=['ordered', 'scheduled', 'in_progress']).count()
            overdue = sum(1 for test in today_tests if test.is_overdue)
            
            # Calculate turnaround times
            completed_tests = today_tests.filter(completed_at__isnull=False)
            turnaround_times = []
            processing_times = []
            
            for test in completed_tests:
                if test.completed_at and test.ordered_at:
                    turnaround_delta = test.completed_at - test.ordered_at
                    turnaround_times.append(turnaround_delta.total_seconds() / 3600)  # hours
                
                if test.completed_at and test.started_at:
                    processing_delta = test.completed_at - test.started_at
                    processing_times.append(processing_delta.total_seconds() / 60)  # minutes
            
            avg_turnaround = sum(turnaround_times) / len(turnaround_times) if turnaround_times else 0
            avg_processing = sum(processing_times) / len(processing_times) if processing_times else 0
            
            # Priority breakdown
            stat_count = today_tests.filter(priority='stat').count()
            urgent_count = today_tests.filter(priority='urgent').count()
            routine_count = today_tests.filter(priority='routine').count()
            
            # Update or create analytics
            analytics, created = LabAnalytics.objects.get_or_create(
                lab_department=lab_dept,
                date=today,
                defaults={
                    'total_tests_ordered': total_ordered,
                    'tests_completed': completed,
                    'tests_pending': pending,
                    'tests_overdue': overdue,
                    'avg_turnaround_time': avg_turnaround,
                    'avg_processing_time': avg_processing,
                    'stat_tests': stat_count,
                    'urgent_tests': urgent_count,
                    'routine_tests': routine_count,
                }
            )
            
            if not created:
                analytics.total_tests_ordered = total_ordered
                analytics.tests_completed = completed
                analytics.tests_pending = pending
                analytics.tests_overdue = overdue
                analytics.avg_turnaround_time = avg_turnaround
                analytics.avg_processing_time = avg_processing
                analytics.stat_tests = stat_count
                analytics.urgent_tests = urgent_count
                analytics.routine_tests = routine_count
                analytics.save()
    
    def run_maintenance_tasks(self):
        """Run all lab maintenance tasks"""
        self.process_overdue_tests()
        self.update_daily_analytics()
    
    def cancel_lab_test(self, lab_test, reason=''):
        """Cancel a lab test and notify patient and staff"""
        lab_test.status = 'cancelled'
        lab_test.save()
        self.notification_service.create_and_send_notification(
            user=lab_test.patient.user,
            notification_type='test_cancelled',
            title='Lab Test Cancelled',
            message=f'Your lab test {lab_test.get_test_type_display()} has been cancelled. Reason: {reason}',
            channel='sms'
        )
        if lab_test.ordered_by:
            self.notification_service.create_and_send_notification(
                user=lab_test.ordered_by.user,
                notification_type='test_cancelled',
                title='Lab Test Cancelled',
                message=f'Lab test for {lab_test.patient.user.get_full_name()} has been cancelled. Reason: {reason}',
                channel='email'
            )
