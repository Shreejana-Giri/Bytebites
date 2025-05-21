"""
ASGI config for bytebites project.
"""

import os
import django

# Set the Django settings module explicitly
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bytebites.settings')

# Initialize Django before importing other components
django.setup()

# Import components after Django is set up
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import nutrition.routing

# Create the ASGI application
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            nutrition.routing.websocket_urlpatterns
        )
    ),
})
