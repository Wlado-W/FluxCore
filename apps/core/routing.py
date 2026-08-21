"""Channels websocket routes (live node status и т.п.)."""
from django.urls import path

# from apps.core.consumers import NodeStatusConsumer

websocket_urlpatterns = [
    # path("ws/nodes/status/", NodeStatusConsumer.as_asgi()),
]
