@echo off
echo Starting Daphne ASGI server...
set DJANGO_SETTINGS_MODULE=bytebites.settings
daphne -b 127.0.0.1 -p 8001 bytebites.asgi:application
