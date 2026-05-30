from datetime import timedelta

from django.utils import timezone

from payments.models import Order, Status


def clear_unprocessed_orders():
    queryset = Order.objects.filter(
        status__in=(Status.PENDING, Status.FAILED),
        created_at__lt=timezone.now() - timedelta(hours=2),
    )

    queryset.delete()
