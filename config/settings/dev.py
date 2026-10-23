"""Ustawienia deweloperskie (DJANGO_DEBUG domyślnie włączony)."""

from .base import *  # noqa: F401,F403

DEBUG = True

# W developmencie/testach akceptujemy dowolny host (runserver, test client).
if not ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS = ["*"]

# Bramka odwiedzających demo: lokalnie i w CI (manage.py test) domyślnie wyłączona;
# na produkcji (DJANGO_DEBUG=0) domyślnie włączona — patrz base.py.
DEMO_VISITOR_GATE = env_bool("DEMO_VISITOR_GATE", False)  # noqa: F405
