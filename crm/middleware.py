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
        else:
            user_tz = "Europe/Prague"

        timezone.activate(user_tz)

        return self.get_response(request)
