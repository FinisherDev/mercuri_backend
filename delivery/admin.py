from django.contrib import admin
from .models import Order, Rider

# Register your models here.

class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer', 'rider', 'status', 'created_at', 'accepted_at', 'delivered_at')
    ordering = ('-created_at', )

admin.site.register(Order, OrderAdmin)
admin.site.register(Rider)