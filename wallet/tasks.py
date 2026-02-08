import requests

from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
#from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Wallet, Transaction, WithdrawalRequest
from .services import flutterwave as flw_srv

@shared_task(bind = True, max_retries = 3, default_retry_delay = 15)
def process_withdrawal(self, withdrawal_id):
    try:
        withdrawal = WithdrawalRequest.objects.select_for_update().get(id = withdrawal_id)
    except WithdrawalRequest.DoesNotExist:
        return 
    
    if withdrawal.status != 'pending':
        return
    
    withdrawal.status = 'processing'
    withdrawal.save()
    reference = f"wd_{withdrawal.id}"

    try:
        transfer = flw_srv.initiate_transfer(
            account_number = withdrawal.bank_account_number, 
            bank_code = withdrawal.bank_code, 
            amount = float(withdrawal.amount), 
            reference= reference
            )
        print(transfer)
        
        if transfer.get("status") != "success":
            raise Exception(f"Flutterwave Error: {transfer.get('message')}")
        
        withdrawal.status = "completed"
        withdrawal.save()

    except Exception as exc:
        withdrawal.status = 'failed'
        withdrawal.faliure_reason = str(exc)
        withdrawal.save()

        with transaction.atomic():
            wallet = withdrawal.wallet
            wallet.balance += withdrawal.amount
            wallet.save()
            Transaction.objects.create(wallet = wallet, amount = withdrawal.amount, transaction_format = 'release')
        return
    
