"""URLs de l'app notifications (montées sous /api/v1/notifications/)."""
from django.urls import path

from .views import (
    AdhanSoundsView,
    SubscribeView,
    SubscriptionStatusView,
    TestNotificationView,
    VapidKeyView,
)

urlpatterns = [
    path("adhan-sounds/", AdhanSoundsView.as_view(), name="adhan-sounds"),
    path("vapid-key/", VapidKeyView.as_view(), name="vapid-key"),
    path("subscribe/", SubscribeView.as_view(), name="subscribe"),
    path("status/", SubscriptionStatusView.as_view(), name="subscription-status"),
    path("test/", TestNotificationView.as_view(), name="test-notification"),
]
