import base64
import hashlib

import ecdsa
import requests
from django.conf import settings

from .models import Order, Payment, Status

API_INVOICE_URL = "https://api.monobank.ua/api/merchant/invoice/create"
API_RECEIPT_URL = "https://api.monobank.ua/api/merchant/receipt"


class MonobankService:
    def __init__(self):
        self.headers = {
            "X-Token": settings.MONOBANK_TOKEN,
            "Content-Type": "application/json",
        }

    def create_invoice(self, order: Order) -> str:
        amount_in_cents = int(order.total_amount * 100)
        price_per_lesson_in_cents = int(order.price_per_lesson * 100)

        payload = {
            "amount": amount_in_cents,
            "ccy": 980,
            "merchantInvoiceId": str(order.id),
            "redirectUrl": f"{settings.BASE_URL}/payment/success/",
            "webHookUrl": f"{settings.BASE_URL}/payment/webhook/",
            "basket": [
                {
                    "name": f"Czech Lesson x{order.lessons_quantity}",
                    "qty": order.lessons_quantity,
                    "sum": price_per_lesson_in_cents,
                    "unit": "pcs",
                    "code": "001",
                }
            ],
            "initiationKind": "client",
            "validity": 60 * 60 * 2,
        }

        response = requests.post(API_INVOICE_URL, json=payload, headers=self.headers)
        response.raise_for_status()
        data = response.json()

        Payment.objects.create(
            order=order,
            external_id=data["invoiceId"],
            amount=order.total_amount,
            status="CREATED",
            raw_response=data,
        )

        order.status = Status.PENDING
        order.save()

        return data["pageUrl"]


def validate_sign(x_sign_base64: str, body_bytes: bytes) -> bool:
    if not x_sign_base64:
        return False

    try:
        pubkey_response = requests.get(
            "https://api.monobank.ua/api/merchant/pubkey",
            headers={"X-token": settings.MONOBANK_TOKEN},
        )
        pub_key_base64 = ""

        if pubkey_response.status_code == 200:
            pub_key_base64 = pubkey_response.json().get("key")
            if not pub_key_base64:
                raise Exception("Some error occured")

        pub_key_bytes = base64.b64decode(pub_key_base64)
        signature_bytes = base64.b64decode(x_sign_base64)
        pub_key = ecdsa.VerifyingKey.from_pem(pub_key_bytes.decode())

        return pub_key.verify(
            signature_bytes,
            body_bytes,
            sigdecode=ecdsa.util.sigdecode_der,
            hashfunc=hashlib.sha256,
        )
    except ecdsa.BadSignatureError:
        return False
    except:
        return False


def send_receipt(order: Order) -> None:
    payment_id = order.payment.external_id

    payload = {
        "invoiceId": payment_id,
        "email": order.customer_email,
    }

    requests.get(
        API_RECEIPT_URL, params=payload, headers={"X-Token": settings.MONOBANK_TOKEN}
    )
