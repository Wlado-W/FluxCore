from django.urls import path
from . import views

app_name = "backup"

urlpatterns = [
    path("", views.BackupListView.as_view(), name="list"),
    path("create/", views.BackupCreateView.as_view(), name="create"),
    path("<int:pk>/download/", views.BackupDownloadView.as_view(), name="download"),
    path("<int:pk>/", views.BackupDeleteView.as_view(), name="delete"),
    path("<int:pk>/restore/", views.BackupRestoreView.as_view(), name="restore"),
]
