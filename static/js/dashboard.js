/**
 * Подключение к WebSocket дашборда: живое обновление статуса/метрик нод
 * без перезагрузки страницы. Сервер шлёт события через
 * apps.core.consumers.NodeStatusConsumer (group "nodes_status").
 */
(function () {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const socketUrl = `${protocol}//${window.location.host}/ws/nodes/status/`;

    let socket;
    let reconnectDelay = 1000;

    function connect() {
        socket = new WebSocket(socketUrl);

        socket.onopen = () => {
            reconnectDelay = 1000;
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            updateNodeCard(data);
        };

        socket.onclose = () => {
            setTimeout(connect, reconnectDelay);
            reconnectDelay = Math.min(reconnectDelay * 2, 30000);
        };
    }

    function updateNodeCard(data) {
        const card = document.getElementById(`node-card-${data.node_id}`);
        if (!card) return;

        card.dataset.status = data.status;

        const statusBadge = document.getElementById(`node-status-${data.node_id}`);
        if (statusBadge) {
            statusBadge.className = `node-status-badge status-${data.status}`;
            statusBadge.textContent = statusLabel(data.status);
        }

        setMetric(`node-cpu-${data.node_id}`, data.cpu_percent);
        setMetric(`node-ram-${data.node_id}`, data.ram_percent);
        setMetric(`node-disk-${data.node_id}`, data.disk_percent);

        const lastSeen = document.getElementById(`node-last-seen-${data.node_id}`);
        if (lastSeen && data.last_seen_at) {
            lastSeen.textContent = `Последний отклик: ${new Date(data.last_seen_at).toLocaleString("ru-RU")}`;
        }

        refreshSummaryCounters();
    }

    function setMetric(elementId, value) {
        const el = document.getElementById(elementId);
        if (el && value !== null && value !== undefined) {
            el.textContent = `${Math.round(value)}%`;
        }
    }

    function statusLabel(status) {
        const labels = {
            pending: "Ожидает установки",
            online: "Онлайн",
            offline: "Оффлайн",
            error: "Ошибка",
        };
        return labels[status] || status;
    }

    function refreshSummaryCounters() {
        const cards = document.querySelectorAll(".node-card");
        let online = 0, offline = 0, error = 0;
        cards.forEach((card) => {
            if (card.dataset.status === "online") online++;
            else if (card.dataset.status === "offline") offline++;
            else if (card.dataset.status === "error") error++;
        });
        document.getElementById("summary-online").textContent = online;
        document.getElementById("summary-offline").textContent = offline;
        document.getElementById("summary-error").textContent = error;
    }

    connect();
})();
