# check_employee.py
import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manager.settings')  # <- Замените на имя вашего проекта
django.setup()

from core.models import Employee

def check_employee(employee_id):
    print("\n" + "="*40)
    print("ЗАПУСК ПРОВЕРКИ...")
    
    try:
        emp = Employee.objects.get(id=employee_id)
        print(f"[1] Найден сотрудник: {emp}")
    except Employee.DoesNotExist:
        print(f"\nОШИБКА: Сотрудник с ID {employee_id} не найден!")
        return
    
    print(f"[2] Проверка должности...")
    if not emp.position:
        print("! Нет назначенной должности !")
        return
    
    print(f"[3] Поиск норм...")
    norms = emp.position.norms.all()
    print(f"Найдено норм: {norms.count()}")
    
    print(f"[4] Проверка выдач...")
    issues = emp.issues.filter(is_active=True)
    print(f"Активных выдач: {issues.count()}")
    
    print("\n" + "="*40)
    print("ПРОВЕРКА ЗАВЕРШЕНА")

if __name__ == "__main__":
    check_employee(1)  # <- Тестовый ID, измените на нужный