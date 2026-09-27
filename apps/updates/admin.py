from django.contrib import admin

from .models import SystemPatch, UpdateHistory


@admin.register(SystemPatch)
class SystemPatchAdmin(admin.ModelAdmin):
    list_display = ("patch_id", "title", "source", "status", "is_bash", "applied_at", "created_at")
    list_filter = ("status", "source", "is_bash")
    search_fields = ("patch_id", "title", "description")
    readonly_fields = ("status", "logs", "applied_at", "created_at", "signature")


@admin.register(UpdateHistory)
class UpdateHistoryAdmin(admin.ModelAdmin):
    list_display = ("from_version", "to_version", "status", "started_at", "finished_at")
    list_filter = ("status",)
    readonly_fields = [f.name for f in UpdateHistory._meta.fields]
