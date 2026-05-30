# crm/middleware.py
import zoneinfo
from django.utils import timezone


class UserTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tz_param = request.GET.get("tz")

        if tz_param and tz_param in zoneinfo.available_timezones():
            user_tz = tz_param
            request.session["django_timezone"] = user_tz

        elif "django_timezone" in request.session:
            user_tz = request.session["django_timezone"]

        else:
            user_tz = "Europe/Prague"

        timezone.activate(user_tz)

        return self.get_response(request)
