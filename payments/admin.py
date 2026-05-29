from django.contrib import admin

from payments.models import Order, Payment

admin.site.register(Order)
admin.site.register(Payment)
