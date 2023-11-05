from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = [
    "127.0.0.1",
    "elixir-staging.purplequarter.co",
    "elixir.purplequarter.co",
    "api.elixir.stage.purplequarter.co",
    "localhost",
]
CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOWED_ORIGINS = [
    "https://api.elixir.stage.purplequarter.co",
    "https://staging-api.elixir.purplequarter.co",
    "http://localhost:3000",
    "https://elixir.purplequarter.co",
    "https://elixir-staging.purplequarter.co",
]
CORS_ALLOW_HEADERS = [
    "access-control-allow-origin",
    "content-type",
    "authorization",
    "accept",
]
CSRF_TRUSTED_ORIGINS = [
    "https://api.elixir.stage.purplequarter.co",
    "https://staging-api.elixir.purplequarter.co",
]
SITE_URL = "https://elixir-staging.purplequarter.co"
