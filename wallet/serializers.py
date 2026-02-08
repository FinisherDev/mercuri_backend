from rest_framework import serializers
from .models import Transaction, WithdrawalRequest

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"

class WithdrawalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalRequest
        fields = [
            "id", "amount", "bank_account_name", "bank_account_number",
            "bank_code", "status", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]