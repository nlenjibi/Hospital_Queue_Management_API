from django.core.management.base import BaseCommand
from notifications.services import NotificationService

class Command(BaseCommand):
    help = 'Process scheduled and retry notifications'
    
    def handle(self, *args, **options):
        service = NotificationService()
        
        self.stdout.write('Processing scheduled notifications...')
        service.process_scheduled_notifications()
        
        self.stdout.write('Processing retry notifications...')
        service.process_retry_notifications()
        
        self.stdout.write(
            self.style.SUCCESS('Notification processing completed successfully')
        )
