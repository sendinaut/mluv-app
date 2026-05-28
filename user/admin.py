from django.contrib import admin
from django.contrib.auth import get_user_model

from user.models import InviteCode

admin.site.register(get_user_model())
admin.site.register(InviteCode)
