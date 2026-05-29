import requests
from django.conf import settings
from .models import Order, Status, FiscalStatus


class FiscalizationService:
    API_URL = "https://api.checkbox.ua/api/v1/receipts/sell"

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.FISCAL_API_KEY}",
            "Content-Type": "application/json",
        }

    def fiscalize_order(self, order: Order):
        if order.status != Status.PAID:
            return

        payload = {
            "cashier_name": "Online School",
            "goods": [
                {
                    "code": "001",
                    "name": f"Czech Lesson x{order.lessons_quantity}",
                    "price": int(order.price_per_lesson * 100),
                    "quantity": order.lessons_quantity * 1000,
                    "tax": [],
                }
            ],
            "payments": [{"type": "CARD", "value": int(order.total_amount * 100)}],
            "client": {"email": order.customer_email, "phone": order.customer_phone},
        }

        try:
            response = requests.post(self.API_URL, json=payload, headers=self.headers)
            if response.status_code == 201:
                data = response.json()
                order.fiscal_status = FiscalStatus.DONE
                order.fiscal_receipt_id = data.get("id")
            else:
                order.fiscal_status = FiscalStatus.FAILED

            order.save()
        except Exception:
            order.fiscal_status = FiscalStatus.FAILED
            order.save()
