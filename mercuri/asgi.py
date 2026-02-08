"""
ASGI config for mercuri project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mercuri.settings')
django_asgi_app = get_asgi_application()


from channels.routing import ProtocolTypeRouter, URLRouter
from delivery.middleware import TokenAuthMiddleware
from delivery.routing import websocket_urlpatterns as delivery
from communication.routing import websocket_urlpatterns as communication

url_patterns = delivery + communication

application = ProtocolTypeRouter ({
    "http" : django_asgi_app,
    "websocket" : TokenAuthMiddleware (
        URLRouter (
            url_patterns
        )
    ),
})