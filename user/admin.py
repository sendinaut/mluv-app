from django.contrib import admin
from django.contrib.auth import get_user_model

from user.models import InviteCode, ResetCode

admin.site.register(get_user_model())
admin.site.register(InviteCode)
admin.site.register(ResetCode)
