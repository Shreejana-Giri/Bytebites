#!/bin/bash
echo "Starting Daphne ASGI server..."
export DJANGO_SETTINGS_MODULE=bytebites.settings
daphne -b 127.0.0.1 -p 8001 bytebites.asgi:application
