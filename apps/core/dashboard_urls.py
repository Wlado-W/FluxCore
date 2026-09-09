from django.urls import path

from apps.audit import views as audit_views
from apps.billing import tariff_views
from apps.clients import clientgroup_views, views as client_views
from apps.inbounds import views as inbound_views
from apps.outbounds import views as outbound_views
from apps.routing import views as routing_views

from . import node_views, nodegroup_views, views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_view, name="index"),
    path("nodes/map-data/", views.node_map_data_view, name="node-map-data"),

    path("nodes/manage/", node_views.node_list_view, name="node-list"),
    path("nodes/manage/create/", node_views.node_create_view, name="node-create"),
    path("nodes/manage/<int:pk>/edit/", node_views.node_edit_view, name="node-edit"),
    path("nodes/manage/<int:pk>/delete/", node_views.node_delete_view, name="node-delete"),

    path("nodegroups/manage/", nodegroup_views.nodegroup_list_view, name="nodegroup-list"),
    path("nodegroups/manage/create/", nodegroup_views.nodegroup_create_view, name="nodegroup-create"),
    path("nodegroups/manage/<int:pk>/edit/", nodegroup_views.nodegroup_edit_view, name="nodegroup-edit"),
    path("nodegroups/manage/<int:pk>/delete/", nodegroup_views.nodegroup_delete_view, name="nodegroup-delete"),

    path("inbounds/manage/", inbound_views.inbound_list_view, name="inbound-list"),
    path("inbounds/manage/create/", inbound_views.inbound_create_view, name="inbound-create"),
    path("inbounds/manage/<int:pk>/edit/", inbound_views.inbound_edit_view, name="inbound-edit"),
    path("inbounds/manage/<int:pk>/delete/", inbound_views.inbound_delete_view, name="inbound-delete"),
    path("inbounds/manage/<int:pk>/test/", inbound_views.inbound_test_view, name="inbound-test"),

    path("outbounds/manage/", outbound_views.outbound_list_view, name="outbound-list"),
    path("outbounds/manage/create/", outbound_views.outbound_create_view, name="outbound-create"),
    path("outbounds/manage/<int:pk>/edit/", outbound_views.outbound_edit_view, name="outbound-edit"),
    path("outbounds/manage/<int:pk>/delete/", outbound_views.outbound_delete_view, name="outbound-delete"),

    path("routing/manage/", routing_views.routingrule_list_view, name="routingrule-list"),
    path("routing/manage/create/", routing_views.routingrule_create_view, name="routingrule-create"),
    path("routing/manage/<int:pk>/edit/", routing_views.routingrule_edit_view, name="routingrule-edit"),
    path("routing/manage/<int:pk>/delete/", routing_views.routingrule_delete_view, name="routingrule-delete"),

    path("clients/manage/", client_views.client_list_view, name="client-list"),
    path("clients/manage/create/", client_views.client_create_view, name="client-create"),
    path("clients/manage/<int:pk>/edit/", client_views.client_edit_view, name="client-edit"),
    path("clients/manage/<int:pk>/delete/", client_views.client_delete_view, name="client-delete"),

    path("clientgroups/manage/", clientgroup_views.clientgroup_list_view, name="clientgroup-list"),
    path("clientgroups/manage/create/", clientgroup_views.clientgroup_create_view, name="clientgroup-create"),
    path("clientgroups/manage/<int:pk>/edit/", clientgroup_views.clientgroup_edit_view, name="clientgroup-edit"),
    path("clientgroups/manage/<int:pk>/delete/", clientgroup_views.clientgroup_delete_view, name="clientgroup-delete"),

    path("tariffs/manage/", tariff_views.tariff_list_view, name="tariff-list"),
    path("tariffs/manage/create/", tariff_views.tariff_create_view, name="tariff-create"),
    path("tariffs/manage/<int:pk>/edit/", tariff_views.tariff_edit_view, name="tariff-edit"),
    path("tariffs/manage/<int:pk>/delete/", tariff_views.tariff_delete_view, name="tariff-delete"),

    # Аудит-лог (read-only, без Django admin)
    path("audit/", audit_views.auditlog_list_view, name="auditlog-list"),
]
