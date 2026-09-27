from django.contrib import admin

from .models import BackupTask


@admin.register(BackupTask)
class BackupTaskAdmin(admin.ModelAdmin):
    list_display = ("file_name", "status", "is_encrypted", "file_size", "created_by", "created_at")
    list_filter = ("status", "is_encrypted")
    readonly_fields = [f.name for f in BackupTask._meta.fields]

    def has_add_permission(self, request):
        # Бэкапы создаются только через задачу create_system_backup, не вручную в admin
        return False
