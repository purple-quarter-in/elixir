from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "elixir.purplequarter.co", "api.elixir.purplequarter.co"]
CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOWED_ORIGINS = ["https://api.elixir.purplequarter.co", "https://elixir.purplequarter.co"]
CORS_ALLOW_HEADERS = [
    "access-control-allow-origin",
    "content-type",
    "authorization",
    "accept",
]
CSRF_TRUSTED_ORIGINS = ["https://api.elixir.purplequarter.co"]
SITE_URL = "https://elixir.purplequarter.co"
