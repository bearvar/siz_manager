from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import FlushingAgentNorm, FlushingAgentIssue, Employee

class Command(BaseCommand):
    help = 'Process flushing agents according to norms'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Display detailed processing information'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate processing without saving changes'
        )

    def handle(self, *args, **options):
        today = timezone.now().date()
        self.stdout.write(f"Processing flushing agents for {today}")
        
        for norm in FlushingAgentNorm.objects.select_related('position', 'agent_type').all():
            self.process_norm(norm, today, options)
        
        self.stdout.write(self.style.SUCCESS('Successfully processed flushing agents'))

    def process_norm(self, norm, today, options):
        employees = Employee.objects.filter(position=norm.position)
        for employee in employees:
            self.process_employee(employee, norm, today, options)

    def process_employee(self, employee, norm, today, options):
        active_issues = FlushingAgentIssue.objects.filter(
            employee=employee,
            agent_type=norm.agent_type,
            is_active=True
        ).order_by('issue_date')

        self.stdout.write(f"\nProcessing {employee} ({norm.agent_type})")
        self.stdout.write(f"Active issues: {len(active_issues)}")
        
        required_ml = norm.monthly_ml
        total_available = sum(issue.volume_ml for issue in active_issues)
        
        self.stdout.write(f"Monthly requirement: {required_ml}ml, Total available: {total_available}ml")

        if total_available < required_ml:
            self.stdout.write(f"! Not enough stock, need {required_ml}ml but have {total_available}ml")
            return

        remaining = required_ml
        self.stdout.write(f"Need to consume {remaining}ml from {len(active_issues)} issues")
        
        for idx, issue in enumerate(active_issues, 1):
            if remaining <= 0:
                break

            self.stdout.write(f"\nIssue #{idx} (ID: {issue.id})")
            self.stdout.write(f"Issued: {issue.issue_date}, Volume: {issue.volume_ml}ml")
            
            consumable = min(issue.volume_ml, remaining)
            self.stdout.write(f"Will consume {consumable}ml from this issue")
            
            issue.volume_ml -= consumable
            remaining -= consumable

            if issue.volume_ml <= 0:
                issue.is_active = False
                issue.consumption_date = today
                self.stdout.write("Marking issue as fully consumed")
            else:
                self.stdout.write(f"Remaining in issue: {issue.volume_ml}ml")

            if not options['dry_run']:
                issue.save()
                self.stdout.write("✓ Saved changes")
            else:
                self.stdout.write("◊ Dry-run - no changes saved")
