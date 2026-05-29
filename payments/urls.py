from django.urls import path
from django.views.generic import TemplateView

from payments.views import MonobankWebhookView, StudentBillingView

app_name = "payments"

urlpatterns = [
    path("payment/create/", StudentBillingView.as_view(), name="payment_create"),
    path("payment/webhook/", MonobankWebhookView.as_view(), name="payment_webhook"),
    path(
        "payment/success/",
        TemplateView.as_view(template_name="payments/success.html"),
        name="payment_success",
    ),
]
