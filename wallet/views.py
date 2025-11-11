import requests
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import User
from .models import Wallet, Transaction
from .serializers import TransactionSerializer

# Create your views here.

class WalletView(APIView):
    """
        Wallet API for balance checks and deposits
    """
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        """Retrieve the wallet balance for the authenticated user."""
        try:
            wallet = Wallet.objects.get(user=request.user)
            return Response({"balance": wallet.balance}, status=status.HTTP_200_OK)
        except Wallet.DoesNotExist:
            return Response({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        """Initiate a deposit transaction using Flutterwave."""
        try:
            amount = float(request.data.get("amount"))
            if amount <= 0:
                return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)
            # Call Flutterwave API to process payment
            else:
                flw_response = self.initiate_payment(request.user, amount)
                return Response(flw_response, status=status.HTTP_200_OK)
        except ValueError:
            return Response({"error": "Invalid input"}, status=status.HTTP_400_BAD_REQUEST)

    def initiate_payment(self, user, amount):
        """Send payment request to Flutterwave API."""
        url = "https://api.flutterwave.com/v3/payments"
        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "tx_ref": f"tx_{user.id}_{amount}",
            "amount": amount,
            "currency": "NGN",
            "redirect_url": "http://localhost:8000/api/wallet/callback",
            "customer": {
                "email": user.email,
                "name": user.get_full_name(),
                "phone_number": user.phone_number,
            },
            "meta": {
                "wallet_user_id": user.id
            },
            "customizations":{
                "title":"Wallet Deposit"
            },
        }
        response = requests.post(url, json=data, headers=headers)
        return response.json()
    
class TransferFundsView(APIView):
    """
        Facilitates wallet-wallet transfers
    """

    permission_classes = (IsAuthenticated, )
    
    def post(self, request):
        recipient_account_number = request.data.get("recipient")
        sender = request.user
        amount = float(request.data.get("amount"))
        pin = request.data.get("pin")

        if not sender_wallet.check_transfer_pin(pin):
            return Response({"error": "Invalid PIN"}, status=403)

        if recipient_account_number and amount > 0:
            with transaction.atomic():
                recipient_wallet = Wallet.objects.select_for_update().get(account_number=recipient_account_number)
                sender_wallet = Wallet.objects.select_for_update().get(user = sender)

                if sender_wallet.transfer(amount, recipient_wallet):
                    Transaction.objects.create(wallet=sender_wallet, transaction_type='debit', transaction_format= 'transfer', amount=amount, description=f"Transferred to {recipient_wallet.user}")
                    Transaction.objects.create(wallet=recipient_wallet, transaction_type='credit', transaction_format= 'transfer', amount=amount, description=f"Recieved from {sender}")
            return Response({"message": "Transfer Successful"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

class PINCreationView(APIView):
    """
        API view for PIN creation
    """
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        pin = request.data.get("pin")

        wallet = Wallet.objects.get(user=request.user)

        if pin.len() > 4 :
            return Response({"error" : "PIN maximum length exceeded"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            wallet.set_transfer_pin(pin)
            return Response({"message" : "PIN created successfully"}, status=status.HTTP_200_OK)
class TransactionsView(APIView):
    """
        Wallet API for balance checks and deposits
    """
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        """Retrieve the wallet balance for the authenticated user."""
        try:
            wallet = Wallet.objects.get(user=request.user)
            transactions = Transaction.objects.filter(wallet=wallet)
            serializer = TransactionSerializer(transactions, many = True)
            return Response(serializer.data)
        except Wallet.DoesNotExist:
            return Response({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)

class FlutterwaveCallbackView(APIView):
    """Handle the webhook callback from Flutterwave after payment."""
    def get(self, request):
        tx_ref = request.GET.get("tx_ref")
        email = request.user.email

        if request.GET.get('status') == "successful":
            try:
                response = requests.get (
                    f"https://api.flutterwave.com/v3/transactions/verify_by_reference?tx_ref={tx_ref}",
                    headers = {"Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}"}
                    )
                result = response.json()
                if result["status"] != "success":
                    return Response({"error" : "Transaction verification failed."})

                with transaction.atomic():
                    wallet = Wallet.objects.select_for_update().get(user_id=request.user)
                    wallet.deposit(result["data"]["amount"])
                    Transaction.objects.create(
                        wallet=wallet, 
                        transaction_type='credit', 
                        transaction_format= 'deposit',
                        #status = 'success',
                        amount = result["data"]["amount"], 
                        description=f"{result["data"]["amount"]} deposited by {email}"
                        )
                return Response({"message": "Deposit Successful"}, status=status.HTTP_200_OK)
            except Wallet.DoesNotExist:
                return Response({"error": "Wallet not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)