# Клининговая служба · Вариант 24

Работы 7–9. Топытгин Илья Денисович, ИСдо-44.

Основа: модели и миграции работы 5, макеты работы 6.

## Запуск

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

База, медиафайлы, секреты и виртуальное окружение исключены из Git.
Демонстрационные данные создаются командой seed_demo.
