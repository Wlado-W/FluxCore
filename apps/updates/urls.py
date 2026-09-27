from django.urls import path
from . import views

app_name = "updates"

urlpatterns = [
    path("check/", views.UpdateCheckView.as_view(), name="check"),
    path("apply/", views.UpdateApplyView.as_view(), name="apply"),
    path("history/", views.UpdateHistoryListView.as_view(), name="history"),
    path("patches/", views.SystemPatchListView.as_view(), name="patch-list"),
    path("patches/<int:pk>/", views.SystemPatchDetailView.as_view(), name="patch-detail"),
    path("patches/<int:pk>/apply/", views.SystemPatchApplyView.as_view(), name="patch-apply"),
]
