from django.urls import path

from .views import LoadHeatmapView, NodeForecastView, TopClientsView

app_name = "monitoring"

urlpatterns = [
    path("heatmap/", LoadHeatmapView.as_view(), name="heatmap"),
    path("top-clients/", TopClientsView.as_view(), name="top-clients"),
    path("forecast/<int:node_id>/", NodeForecastView.as_view(), name="forecast"),
]
