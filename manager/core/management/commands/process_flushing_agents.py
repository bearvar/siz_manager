from django.core.management.base import BaseCommand
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.db import transaction, models
from core.models import (
    FlushingAgentNorm,
    FlushingAgentIssue,
    Employee,
    FlushingAgentTransaction,
    TransactionDetail
)

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

class Command(BaseCommand):
    help = 'Process flushing agent consumption according to FIFO principle'

    def handle(self, *args, **options):
        current_date = timezone.now().date()
        self.stdout.write(f"Processing consumption up to {current_date.strftime('%Y-%m-%d')}")
        
        with transaction.atomic():
            # Reset all data to initial state
            self.stdout.write("Resetting all issues and transactions...")
            FlushingAgentIssue.objects.update(
                volume_ml=models.F('volume_ml_nominal'),
                is_active=True,
                consumption_date=None
            )
            FlushingAgentTransaction.objects.all().delete()
            TransactionDetail.objects.all().delete()

            employees = Employee.objects.filter(
                position__isnull=False
            ).prefetch_related('flushingagentissue_set')
            
            total_processed = 0
            
            for employee in employees:
                if not employee.position:
                    continue
                
                for norm in FlushingAgentNorm.objects.filter(position=employee.position):
                    months = get_months_to_process(employee, norm.agent_type, current_date)
                    
                    for month in months:
                        # Process each month with fresh transaction
                        with transaction.atomic():
                            monthly_transaction = FlushingAgentTransaction.objects.create(
                                reference_month=month,
                                employee=employee,
                                agent_type=norm.agent_type,
                                total_consumed=0
                            )

                            issues = FlushingAgentIssue.objects.filter(
                                employee=employee,
                                agent_type=norm.agent_type,
                                is_active=True
                            ).order_by('issue_date')

                            remaining_volume = norm.monthly_ml
                            processed_messages = []

                            for issue in issues:
                                if remaining_volume <= 0:
                                    break

                                consumed = min(issue.volume_ml, remaining_volume)
                                original_volume = issue.volume_ml
                                
                                # Update issue
                                issue.volume_ml -= consumed
                                if issue.volume_ml <= 0:
                                    issue.is_active = False
                                    issue.consumption_date = month
                                issue.save()

                                # Record transaction detail
                                TransactionDetail.objects.create(
                                    transaction=monthly_transaction,
                                    issue=issue,
                                    consumed_volume=consumed,
                                    previous_volume=original_volume,
                                    was_active=True
                                )

                                monthly_transaction.total_consumed += consumed
                                remaining_volume -= consumed

                                processed_messages.append(
                                    f"{month.strftime('%Y-%m')}: Consumed {consumed}ml from {issue.item_name}"
                                )

                            monthly_transaction.save()
                            
                            if processed_messages:
                                total_processed += 1
                                self.stdout.write(f"\n{employee} - {norm.agent_type}:")
                                for msg in processed_messages:
                                    self.stdout.write(f"  {msg}")

        self.stdout.write(f"\nProcessing complete. Updated {total_processed} records.")
