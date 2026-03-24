#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    env_path = PROJECT_ROOT / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'road_signes_test.settings')

try:
    django.setup()
except ImportError:
    print("Ошибка: Django не установлен в текущем окружении.")
    print("Установите: pip install django")
    sys.exit(1)
except Exception as e:
    print(f"Ошибка при инициализации Django: {e}")
    sys.exit(1)

from django.contrib.auth import get_user_model
from django.db.utils import OperationalError, ProgrammingError
from django.core.exceptions import ImproperlyConfigured

User = get_user_model()
username = os.environ.get('ADMIN_USERNAME', 'admin')
email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
password = os.environ.get('ADMIN_PASSWORD', 'admin123')

def create_superuser():
    try:
        User.objects.exists()
    except (OperationalError, ProgrammingError) as e:
        print("Ошибка: таблицы Django не созданы. Возможно, не выполнены миграции.")
        print("Выполните: python manage.py migrate")
        print(f"Детали: {e}")
        return False

    if User.objects.filter(username=username).exists():
        print(f"Суперпользователь '{username}' уже существует.")
        return True

    try:
        User.objects.create_superuser(username, email, password)
        print(f"Суперпользователь '{username}' успешно создан!")
        return True
    except TypeError as e:
        print(f"Ошибка: не удалось создать суперпользователя. Возможно, ваша модель пользователя требует дополнительные поля.")
        print(f"Детали: {e}")
        try:
            all_fields = [f.name for f in User._meta.get_fields()]
            print(f"Доступные поля: {', '.join(all_fields)}")
        except:
            pass
        return False
    except Exception as e:
        print(f"Непредвиденная ошибка при создании суперпользователя: {e}")
        import traceback
        traceback.print_exc()
        return False
if __name__ == '__main__':
    success = create_superuser()
    sys.exit(0 if success else 1)