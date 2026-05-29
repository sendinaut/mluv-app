import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin

from crm.models import Student
from .forms import PaymentInformationForm
from .models import Order, Payment, FiscalStatus, Status
from .services import MonobankService, validate_sign

User = get_user_model()


class StudentBillingView(LoginRequiredMixin, View):
    def get(self, request):
        student_crm = Student.objects.filter(student_user=request.user)
        if not student_crm.exists():
            return HttpResponse("Профіль студента не знайдено в CRM", status=404)

        tutors = list({student.teacher for student in student_crm if student.teacher})

        form = PaymentInformationForm(
            initial={
                "email": request.user.email,
                "full_name": getattr(request.user, "full_name", "") or "",
                "phone_number": getattr(request.user, "phone_number", "") or "",
            }
        )

        return render(
            request,
            "payments/billing.html",
            {"form": form, "tutors": tutors, "student_crm": student_crm},
        )

    def post(self, request):
        student_crm = Student.objects.filter(student_user=request.user)
        if not student_crm.exists():
            return HttpResponse("Профіль студента не знайдено в CRM", status=404)

        form = PaymentInformationForm(request.POST)

        if form.is_valid():
            tutor_id = request.POST.get("tutor_id")

            lessons_count_raw = request.POST.get("lessons_count")
            lessons_count = int(lessons_count_raw) if lessons_count_raw else 5

            if not tutor_id:
                messages.error(request, "Будь ласка, оберіть репетитора.")
                return redirect("payments:billing")

            tutor = get_user_model().objects.get(id=tutor_id)

            if not tutor:
                messages.error(
                    request, "Вказаний репетитор не зв'язаний з вашим профілем."
                )
                return redirect("payments:billing")

            user = request.user
            user.email = form.cleaned_data["email"]
            user.full_name = form.cleaned_data["full_name"]
            user.phone_number = form.cleaned_data["phone_number"]
            user.save()

            price_per_lesson = getattr(tutor, "lesson_price", Decimal("400.00"))

            order = Order.objects.create(
                user=user,
                lessons_quantity=lessons_count,
                price_per_lesson=price_per_lesson,
                status=Status.PENDING,
            )

            try:
                mono_service = MonobankService()
                payment_url = mono_service.create_invoice(order)
                return redirect(payment_url)

            except Exception as e:
                form.add_error(None, f"Помилка платіжної системи Monobank: {e}")

        return self.get(request)


class MonobankWebhookView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        x_sign_base64 = request.headers.get("x-sign") or request.headers.get("X-Sign")
        body_bytes = request.body

        if not validate_sign(x_sign_base64, body_bytes):
            return HttpResponse("Sign Validation Error", status=400)

        try:
            data = json.loads(body_bytes)

            invoice_id = data.get("invoiceId")
            status = data.get("status")

            try:
                transaction = Payment.objects.select_related("order__user").get(
                    external_id=invoice_id
                )
            except Payment.DoesNotExist:
                return HttpResponse("Transaction not found", status=404)

            transaction.status = status
            transaction.raw_response = data
            transaction.save()

            order = transaction.order
            user = order.user

            if status == "success":
                order.status = Status.PAID
                order.fiscal_status = FiscalStatus.PENDING
                order.save()

                wallet_data = data.get("walletData", {})
                payment_info = data.get("paymentInfo", {})

                card_token = wallet_data.get("cardToken")
                masked_pan = payment_info.get("maskedPan")

                if card_token:
                    user.card_token = card_token
                    user.masked_pan = masked_pan
                    user.save(update_fields=["card_token", "masked_pan"])

            elif status in ["failure", "reversed"]:
                order.status = Status.FAILED
                order.save()

            return HttpResponse("OK", status=200)

        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", status=400)
