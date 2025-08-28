from django.core.management.base import BaseCommand
from notifications.models import NotificationTemplate

class Command(BaseCommand):
    help = 'Create default notification templates'
    
    def handle(self, *args, **options):
        templates = [
            {
                'name': 'queue_position_update',
                'type': 'queue_update',
                'channel': 'sms',
                'title_template': 'Queue Update - {queue_name}',
                'message_template': 'Hi {patient_name}, you are now #{position} in line for {queue_name}. Estimated wait time: {estimated_wait} minutes.',
                'variables': {'patient_name': 'Patient full name', 'queue_name': 'Queue name', 'position': 'Position in queue', 'estimated_wait': 'Wait time in minutes'}
            },
            {
                'name': 'consultation_ready',
                'type': 'consultation_ready',
                'channel': 'sms',
                'title_template': 'Ready for Consultation',
                'message_template': 'Hi {patient_name}, please proceed to {department} for your consultation. You are next!',
                'variables': {'patient_name': 'Patient full name', 'department': 'Department name', 'queue_name': 'Queue name'}
            },
            {
                'name': 'delay_alert',
                'type': 'delay_alert',
                'channel': 'sms',
                'title_template': 'Appointment Delay',
                'message_template': 'Hi {patient_name}, there is a {delay_minutes} minute delay for {queue_name}. New estimated time: {new_estimated_time}.',
                'variables': {'patient_name': 'Patient full name', 'queue_name': 'Queue name', 'delay_minutes': 'Delay in minutes', 'new_estimated_time': 'New estimated time'}
            },
            {
                'name': 'lab_results_ready',
                'type': 'lab_results',
                'channel': 'email',
                'title_template': 'Lab Results Ready - {test_type}',
                'message_template': 'Hi {patient_name}, your {test_type} results are ready. Please contact your healthcare provider to discuss the results.',
                'variables': {'patient_name': 'Patient full name', 'test_type': 'Type of lab test', 'completed_at': 'Test completion time'}
            }
        ]
        
        for template_data in templates:
            template, created = NotificationTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            
            if created:
                self.stdout.write(f"Created template: {template.name}")
            else:
                self.stdout.write(f"Template already exists: {template.name}")
        
        self.stdout.write(
            self.style.SUCCESS('Notification templates created successfully')
        )
