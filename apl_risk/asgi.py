"""ASGI config for the APL risk project."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apl_risk.settings")

application = get_asgi_application()
