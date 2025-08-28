from django.core.management.base import BaseCommand
from labs.services import LabManagementService

class Command(BaseCommand):
    help = 'Run lab maintenance tasks (overdue tests, analytics)'
    
    def handle(self, *args, **options):
        service = LabManagementService()
        
        self.stdout.write('Starting lab maintenance tasks...')
        
        # Run maintenance tasks
        service.run_maintenance_tasks()
        
        self.stdout.write(
            self.style.SUCCESS('Lab maintenance tasks completed successfully')
        )
