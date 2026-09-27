"""
Django Channels consumer для live-обновлений статуса нод на дашборде.

Все подключённые клиенты (админы, смотрящие дашборд) состоят в общей
group "nodes_status". Когда Celery-задача check_node_health/collect_node_metrics
обновляет ноду, она публикует событие в эту group (через channel layer) —
и все открытые дашборды обновляются в реальном времени без перезагрузки.
"""
from channels.generic.websocket import AsyncJsonWebsocketConsumer

NODES_STATUS_GROUP = "nodes_status"


class NodeStatusConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        if not self.scope["user"].is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(NODES_STATUS_GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(NODES_STATUS_GROUP, self.channel_name)

    # Обработчик событий типа "node.status.update", отправляемых через
    # channel_layer.group_send(NODES_STATUS_GROUP, {"type": "node.status.update", ...})
    async def node_status_update(self, event):
        await self.send_json({
            "node_id": event["node_id"],
            "status": event["status"],
            "cpu_percent": event.get("cpu_percent"),
            "ram_percent": event.get("ram_percent"),
            "disk_percent": event.get("disk_percent"),
            "last_seen_at": event.get("last_seen_at"),
        })
