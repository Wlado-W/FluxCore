from django.urls import path

from . import node_views, views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_view, name="index"),
    path("nodes/map-data/", views.node_map_data_view, name="node-map-data"),

    # Кастомный CRUD для нод (без Django admin)
    path("nodes/manage/", node_views.node_list_view, name="node-list"),
    path("nodes/manage/create/", node_views.node_create_view, name="node-create"),
    path("nodes/manage/<int:pk>/edit/", node_views.node_edit_view, name="node-edit"),
    path("nodes/manage/<int:pk>/delete/", node_views.node_delete_view, name="node-delete"),
]
