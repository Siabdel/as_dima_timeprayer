"""Administration des abonnements push et du journal de notifications."""
from django.contrib import admin

from .models import PrayerNotificationLog, PushSubscription


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "endpoint", "created_at", "last_error_at")
    search_fields = ("user__email", "endpoint")
    readonly_fields = ("created_at", "renewed_at")


@admin.register(PrayerNotificationLog)
class PrayerNotificationLogAdmin(admin.ModelAdmin):
    list_display = ("user", "prayer_name", "date", "status", "sent_at")
    list_filter = ("status", "prayer_name")
    search_fields = ("user__email",)
