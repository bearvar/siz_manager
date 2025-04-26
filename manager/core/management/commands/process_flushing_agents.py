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

def get_reference_date():
    """Get first day of previous month for processing"""
    today = timezone.now().date()
    if today.day == 1:
        return (today - relativedelta(months=1)).replace(day=1)
    return today.replace(day=1) - relativedelta(days=1)

def process_employee_flushing(employee, reference_date):
    """Process flushing agents for a single employee"""
    processed = []
    
    # Get all agent types with norms for this employee's position
    if not employee.position:
        return processed

    # Check for existing transactions for this reference month
    existing_transactions = FlushingAgentTransaction.objects.filter(
        reference_month=reference_date,
        employee=employee
    ).prefetch_related('details')

    # Rollback existing transactions if found
    if existing_transactions.exists():
        for transaction in existing_transactions:
            for detail in transaction.details.all():
                issue = detail.issue
                issue.volume_ml += detail.consumed_volume
                issue.is_active = detail.was_active
                if issue.volume_ml == 0:
                    issue.consumption_date = None
                issue.save()
            transaction.delete()
        processed.append("Отменены предыдущие списания за этот месяц")

    agent_norms = FlushingAgentNorm.objects.filter(
        position=employee.position
    ).select_related('agent_type')
    
    for norm in agent_norms:
        # Get active issues for this agent type ordered by issue date (FIFO)
        issues = FlushingAgentIssue.objects.filter(
            employee=employee,
            agent_type=norm.agent_type,
            is_active=True
        ).order_by('issue_date')
        
        required_volume = norm.monthly_ml
        remaining_volume = required_volume
        total_consumed = 0
        
        # Create transaction record
        transaction = FlushingAgentTransaction.objects.create(
            reference_month=reference_date,
            employee=employee,
            agent_type=norm.agent_type,
            total_consumed=0
        )
        
        for issue in issues:
            if remaining_volume <= 0:
                break
                
            available = issue.volume_ml
            original_volume = issue.volume_ml
            was_active = issue.is_active
            
            if available > remaining_volume:
                # Partially consume this issue
                issue.volume_ml -= remaining_volume
                consumed = remaining_volume
                remaining_volume = 0
            else:
                # Fully consume this issue
                consumed = available
                remaining_volume -= available
                issue.volume_ml = 0
                issue.is_active = False
                issue.consumption_date = reference_date
            
            issue.save()
            total_consumed += consumed
            
            # Create transaction detail
            TransactionDetail.objects.create(
                transaction=transaction,
                issue=issue,
                consumed_volume=consumed,
                previous_volume=original_volume,
                was_active=was_active
            )
            
            processed.append(f"Списано {consumed}мл из выдачи {issue.item_name} ({issue.issue_date})")
        
        # Update transaction with total consumed
        transaction.total_consumed = total_consumed
        transaction.save()
        
        if remaining_volume > 0:
            processed.append(f"Внимание! Недостаточно средств по норме {norm.agent_type.name}: не хватило {remaining_volume}мл")
    
    return processed

class Command(BaseCommand):
    help = 'Process flushing agents consumption based on norms'

    def handle(self, *args, **options):
        reference_date = get_reference_date()
        self.stdout.write(f"Обработка расходов моющих средств на {reference_date.strftime('%Y-%m')}")
        
        # Process all active employees
        employees = Employee.objects.filter(position__isnull=False).prefetch_related('flushingagentissue_set')
        
        total_processed = 0
        with transaction.atomic():
            for employee in employees:
                results = process_employee_flushing(employee, reference_date)
                if results:
                    total_processed += 1
                    self.stdout.write(f"\nСотрудник: {employee}")
                    for msg in results:
                        self.stdout.write(f"  {msg}")
        
        self.stdout.write(f"\nОбработка завершена. Затронуто сотрудников: {total_processed}")
