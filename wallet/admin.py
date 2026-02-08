from django.contrib import admin
from .models import Wallet, Transaction, WithdrawalRequest

# Register your models here.

class WalletAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'balance', 'updated_at', 'created_at')
    list_filter = ('created_at', )

class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'bank_account_name', 'bank_account_number', 'created_at')
    list_filter = ('created_at', )
    ordering = ('-created_at', )

admin.site.register(Wallet, WalletAdmin)
admin.site.register(Transaction)
admin.site.register(WithdrawalRequest, WithdrawalAdmin)