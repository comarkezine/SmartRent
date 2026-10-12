"""
WSGI configuration for SmartRent.

Exposes the WSGI application as a module-level variable
named 'application'.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_rental.settings"
)

application = get_wsgi_application()