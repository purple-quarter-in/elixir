"""
WSGI config for elixir project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from elixir.settings.base import ENV

print(f"elixir.settings.{ENV.str('ENV_TYPE')}")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"elixir.settings.{ENV.str('ENV_TYPE')}")
application = get_wsgi_application()
from elixir import schedular

Apschedular = schedular.Schedular()
