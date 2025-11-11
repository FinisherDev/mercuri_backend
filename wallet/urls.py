from django.urls import path
from wallet.views import WalletView, TransferFundsView, TransactionsView, FlutterwaveCallbackView, PINCreationView

urlpatterns = [
    path('', WalletView.as_view(), name='wallet'),
    path('transfer/', TransferFundsView.as_view(), name='transfer'),
    path('pin/', PINCreationView.as_view(), name='pin'),
    path('transactions/', TransactionsView.as_view(), name='transactions'),
    path('callback/', FlutterwaveCallbackView.as_view(), name='callback')
]
