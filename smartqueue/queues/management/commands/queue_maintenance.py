from django.core.management.base import BaseCommand
from queues.services import QueueManagementService

class Command(BaseCommand):
    help = 'Run queue maintenance tasks (no-show processing, notifications, analytics, queue optimization)'
    
    def handle(self, *args, **options):
        service = QueueManagementService()
        
        self.stdout.write('Starting queue maintenance tasks...')
        
        try:
            # Run all maintenance tasks (no-shows, notifications, analytics, optimization)
            service.run_maintenance_tasks()
            self.stdout.write(
                self.style.SUCCESS('Queue maintenance tasks completed successfully')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Queue maintenance failed: {e}')
            )
