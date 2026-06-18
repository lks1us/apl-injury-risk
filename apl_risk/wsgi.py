"""WSGI config for PythonAnywhere and local deployment."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apl_risk.settings")

application = get_wsgi_application()
