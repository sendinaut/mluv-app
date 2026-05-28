from django.conf import settings
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views import View

from user.forms import RegistrationForm
from user.models import InviteCode


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
