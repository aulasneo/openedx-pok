from django.urls import path
from openedx_pok.views import PoKWebhookView

urlpatterns = [
    path("pok/", PoKWebhookView.as_view(), name="pok-webhook"),
]
