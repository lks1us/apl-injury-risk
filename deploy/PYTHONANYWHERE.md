# Деплой на PythonAnywhere (аккаунт L1ksius)

## Ссылка для формы сдачи

**https://l1ksius.pythonanywhere.com**

## 1. Bash-консоль на pythonanywhere.com

```bash
cd ~
git clone https://github.com/lks1us/apl-injury-risk.git
cd apl-injury-risk
mkvirtualenv --python=/usr/bin/python3.10 apl-risk
pip install -r requirements.txt
workon apl-risk
python manage.py migrate
python manage.py seed_demo
python manage.py collectstatic --noinput
```

## 2. Web → Add a new web app

- **Manual configuration**
- **Python 3.10**
- Virtualenv: `/home/L1ksius/.virtualenvs/apl-risk`

## 3. WSGI configuration file

Откройте WSGI-файл на странице Web и замените содержимое на:

```python
import os
import sys

path = "/home/L1ksius/apl-injury-risk"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ["DJANGO_SECRET_KEY"] = "change-me-to-a-long-random-string"
os.environ["DJANGO_DEBUG"] = "False"
os.environ["DJANGO_ALLOWED_HOSTS"] = "L1ksius.pythonanywhere.com,l1ksius.pythonanywhere.com"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apl_risk.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

> Замените `change-me-to-a-long-random-string` на случайную строку (можно сгенерировать: `python -c "import secrets; print(secrets.token_urlsafe(50))"`).

## 4. Static files (страница Web)

| URL       | Directory                              |
|-----------|----------------------------------------|
| `/static/`| `/home/L1ksius/apl-injury-risk/staticfiles` |

## 5. Reload

Нажмите зелёную кнопку **Reload** на странице Web.

## Проверка

- Главная: https://l1ksius.pythonanywhere.com/
- Админка: https://l1ksius.pythonanywhere.com/admin/

Если видите ошибку — откройте **Web → Log files → error log** и проверьте traceback.

## Обновление после изменений в GitHub

```bash
cd ~/apl-injury-risk
git pull
workon apl-risk
python manage.py migrate
python manage.py collectstatic --noinput
```

Затем **Reload** на странице Web.
