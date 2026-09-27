from django.urls import path
from . import views

app_name = "panel_settings"

urlpatterns = [
    path("themes/", views.theme_list_view, name="theme-list"),
    path("themes/add/", views.theme_create_view, name="theme-add"),
    path("themes/<int:pk>/edit/", views.theme_edit_view, name="theme-edit"),
    path("themes/<int:pk>/delete/", views.theme_delete_view, name="theme-delete"),
    path("themes/<int:pk>/activate/", views.theme_activate_view, name="theme-activate"),
]
