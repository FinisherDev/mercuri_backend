from django.contrib import admin
from .models import Wallet, Transaction

# Register your models here.

class WalletAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'balance', 'updated_at', 'created_at')
    list_filter = ('created_at', )

admin.site.register(Wallet, WalletAdmin)
admin.site.register(Transaction)