# APL Injury Risk

Система прогнозирования риска травматизма игроков Английской Премьер-лиги. Проект намеренно упрощен: риск считается по двум понятным показателям — минуты за последние пять матчей и количество предыдущих травм.

## Функциональность

- панель с метриками риска, распределением оценок и графиками;
- каталог игроков с поиском, фильтрами, сортировкой и ORM-агрегациями;
- карточка игрока с динамикой риска и историей оценок;
- формы добавления игроков, нагрузок и медицинских оценок;
- автоматический расчет `risk_score` и `risk_level`;
- аналитика на Pandas: скользящее среднее риска и подготовка данных для графиков;
- Django Admin для всех моделей;
- seed-команда для демонстрационных данных;
- unit-тесты для логики риска, форм и аналитики.

## Стек

- Python 3.10+
- Django 5
- SQLite
- Pandas
- Bootstrap 5
- Chart.js

## Модели данных

- `Club` — клуб АПЛ.
- `Player` — игрок клуба.
- `TrainingLoad` — нагрузка игрока.
- `InjuryAssessment` — медицинская оценка с автоматическим расчетом риска.
- `RotationPlan` — вспомогательная связанная модель, оставленная в архитектуре проекта.

## Формула риска

```text
risk_score = min(100, minutes_component + season_injury_component + career_injury_component + recency_component)
```

Где:

- `minutes_component = min(45, season_minutes / 3420 * 45)` — нагрузка текущего сезона;
- `season_injury_component = min(30, season_injuries * 10)` — травмы в текущем сезоне;
- `career_injury_component = min(20, career_injuries * 3)` — травмы за карьеру;
- `recency_component` — от 0 до 5 в зависимости от давности последней травмы.

Уровни риска: `low` (< 35), `medium` (35–64), `high` (≥ 65).

Подробная схема и сценарии описаны в [TZ.md](TZ.md).

## Локальный запуск

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
set DJANGO_DEBUG=True
set DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

После запуска:

- сайт: `http://127.0.0.1:8000/`
- админка: `http://127.0.0.1:8000/admin/`

Для macOS/Linux переменные окружения задаются так:

```bash
export DJANGO_DEBUG=True
export DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

## Тесты

```bash
python manage.py test
```

## Демо-данные

Команда ниже очищает данные приложения и создает 20 клубов, 100 игроков, записи нагрузок и медицинские оценки риска:

```bash
python manage.py seed_demo
```

Данные демонстрационные и нужны для защиты проекта, графиков и проверки сценариев.

## Настройка для PythonAnywhere

1. Загрузить проект в публичный GitHub-репозиторий.
2. На PythonAnywhere открыть Bash-консоль и клонировать репозиторий.
3. Создать virtualenv и установить зависимости:

```bash
mkvirtualenv --python=/usr/bin/python3.10 apl-risk
pip install -r requirements.txt
```

4. Указать переменные окружения в WSGI-файле или через настройки окружения:

```python
import os
os.environ["DJANGO_SECRET_KEY"] = "your-production-secret"
os.environ["DJANGO_DEBUG"] = "False"
os.environ["DJANGO_ALLOWED_HOSTS"] = "yourusername.pythonanywhere.com"
```

5. Выполнить миграции и заполнить демо-данные:

```bash
python manage.py migrate
python manage.py seed_demo
python manage.py collectstatic
```

6. В настройках Web App указать:

- Source code: путь к проекту;
- Working directory: путь к проекту;
- WSGI file: импорт `apl_risk.wsgi.application`;
- Static files: URL `/static/`, directory `staticfiles`.

## Скриншоты

### Главная панель

![Главная панель](docs/screenshots/dashboard.png)

### Карточка игрока

![Карточка игрока](docs/screenshots/player-detail.png)

## Культура репозитория

В репозиторий не нужно добавлять `venv`, `__pycache__`, `.idea`, `.vscode`, локальную БД `db.sqlite3` и собранную папку `staticfiles`. Они уже перечислены в `.gitignore`.

Для защиты важно сделать регулярные осмысленные коммиты, например:

- `Add Django project structure`
- `Implement injury risk models`
- `Add player filters and analytics dashboard`
- `Create demo seed command`
- `Document deployment steps`
