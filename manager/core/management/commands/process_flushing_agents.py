from django.core.management.base import BaseCommand
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from core.models import (
    FlushingAgentNorm,
    FlushingAgentIssue,
    Employee,
    FlushingAgentTransaction,
    TransactionDetail
)
from django.db import transaction

def get_months_to_process(employee, agent_type, current_date):
    """Calculate all months between first issue and current date"""
    first_issue = FlushingAgentIssue.objects.filter(
        employee=employee,
        agent_type=agent_type,
        is_active=True
    ).order_by('issue_date').first()
    
    if not first_issue:
        return []
        
    start_month = first_issue.issue_date.replace(day=1)
    end_month = current_date.replace(day=1)
    
    months = []
    while start_month <= end_month:
        months.append(start_month)
        start_month += relativedelta(months=1)
    
    return months

def process_monthly_consumption(employee, agent_type, norm, month):
    """Process consumption for a specific month using FIFO principle"""
    with transaction.atomic():
        # Get or create monthly transaction
        monthly_transaction, created = FlushingAgentTransaction.objects.get_or_create(
            reference_month=month,
            employee=employee,
            agent_type=agent_type,
            defaults={'total_consumed': 0}
        )
        
        if not created:
            return []  # Skip already processed months

        issues = FlushingAgentIssue.objects.filter(
            employee=employee,
            agent_type=agent_type,
            is_active=True
        ).order_by('issue_date')

        remaining_volume = norm.monthly_ml
        processed_messages = []

        for issue in issues:
            if remaining_volume <= 0:
                break

            available = issue.volume_ml
            consumed = min(available, remaining_volume)
            
            # Update issue status
            issue.volume_ml -= consumed
            if issue.volume_ml <= 0:
                issue.is_active = False
                issue.consumption_date = month
            
            # Create transaction detail
            TransactionDetail.objects.create(
                transaction=monthly_transaction,
                issue=issue,
                consumed_volume=consumed,
                previous_volume=issue.volume_ml + consumed,
                was_active=True
            )
            
            monthly_transaction.total_consumed += consumed
            remaining_volume -= consumed
            issue.save()

            processed_messages.append(
                f"{month.strftime('%Y-%m')}: Consumed {consumed}ml from {issue.item_name}"
            )

        if remaining_volume > 0:
            processed_messages.append(
                f"{month.strftime('%Y-%m')}: Warning: Shortage of {remaining_volume}ml"
            )

        monthly_transaction.save()
        return processed_messages

class Command(BaseCommand):
    help = 'Process flushing agent consumption according to FIFO principle'

    def handle(self, *args, **options):
        current_date = timezone.now().date()
        self.stdout.write(f"Processing consumption up to {current_date.strftime('%Y-%m-%d')}")
        
        employees = Employee.objects.filter(
            position__isnull=False
        ).prefetch_related('flushingagentissue_set')
        
        total_processed = 0
        with transaction.atomic():
            for employee in employees:
                if not employee.position:
                    continue
                
                for norm in FlushingAgentNorm.objects.filter(position=employee.position):
                    months = get_months_to_process(employee, norm.agent_type, current_date)
                    for month in months:
                        results = process_monthly_consumption(
                            employee,
                            norm.agent_type,
                            norm,
                            month
                        )
                        if results:
                            total_processed += 1
                            self.stdout.write(f"\n{employee} - {norm.agent_type}:")
                            for msg in results:
                                self.stdout.write(f"  {msg}")

        self.stdout.write(f"\nProcessing complete. Updated {total_processed} records.")
