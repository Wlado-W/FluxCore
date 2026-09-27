/**
 * Карта нод на дашборде (Leaflet + OpenStreetMap, без API-ключей).
 * Данные — из /api/agent/nodes/map/ (DRF, требует авторизации сессией,
 * поэтому credentials: 'same-origin' достаточно в браузере).
 */
(function () {
    const statusColors = {
        online: "#33c481",
        offline: "#6b7385",
        error: "#e5484d",
        pending: "#4f7cff",
    };

    const map = L.map("nodes-map", { scrollWheelZoom: false }).setView([20, 0], 2);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 18,
    }).addTo(map);

    fetch("/nodes/map-data/", { credentials: "same-origin" })
        .then((res) => res.json())
        .then((nodes) => {
            if (!nodes.length) return;

            const bounds = [];
            nodes.forEach((node) => {
                const color = statusColors[node.status] || statusColors.pending;
                const marker = L.circleMarker([node.latitude, node.longitude], {
                    radius: 8,
                    color: color,
                    fillColor: color,
                    fillOpacity: 0.8,
                }).addTo(map);

                marker.bindPopup(`<b>${node.name}</b><br>${node.country_code || ""}<br>Статус: ${node.status}`);
                bounds.push([node.latitude, node.longitude]);
            });

            if (bounds.length > 0) {
                map.fitBounds(bounds, { padding: [30, 30], maxZoom: 5 });
            }
        })
        .catch(() => {
            document.getElementById("nodes-map").innerHTML =
                '<p style="padding:16px;color:var(--text-muted)">Не удалось загрузить карту нод.</p>';
        });
})();
