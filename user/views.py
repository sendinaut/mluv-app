from django.conf import settings
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views import View

from user.forms import RegistrationForm, ResetPasswordForm
from user.models import InviteCode, ResetCode


class RegisterView(View):
    template_name = "registration/register.html"

    def get(self, request):
        token = request.GET.get("invite")

        if (
            not token
            or not InviteCode.objects.filter(code=token, is_used=False).exists()
        ):
            return render(
                request,
                "registration/invite_error.html",
                {
                    "error": "Доступ до реєстрації обмежено. Потрібне валідне запрошувальне посилання."
                },
            )

        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        form = RegistrationForm(initial={"invite_token": token})
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(settings.LOGIN_REDIRECT_URL)

        return render(request, self.template_name, {"form": form})


class ChangePasswordView(View):
    template_name = "registration/change_password.html"

    def get(self, request):
        token = request.GET.get("reset_code")

        if (
            not token
            or not ResetCode.objects.filter(code=token, is_used=False).exists()
        ):
            return render(
                request,
                "registration/invite_error.html",
                {"error": "Такого посилання для скидання паролю не існує."},
            )

        form = ResetPasswordForm(initial={"reset_code": token})
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data["reset_code"]
            new_password = form.cleaned_data["password"]

            reset_code_obj = ResetCode.objects.get(code=token, is_used=False)
            user = reset_code_obj.user

            user.set_password(new_password)
            user.save()

            reset_code_obj.delete()

            return redirect(settings.LOGIN_REDIRECT_URL)

        return render(request, self.template_name, {"form": form})
