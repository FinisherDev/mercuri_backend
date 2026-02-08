from django.urls import path, include
from rest_framework.routers import DefaultRouter
from wallet.views import WalletView, TransferFundsView, TransactionsView, FlutterwaveCallbackView, PINCreationView, WithdrawalViewset

router = DefaultRouter()
router.register(r'withdrawal', WithdrawalViewset, 'withdrawals')

urlpatterns = [
    path('', include(router.urls)),
    path('base/', WalletView.as_view(), name='wallet'),
    path('transfer/', TransferFundsView.as_view(), name='transfer'),
    path('pin/', PINCreationView.as_view(), name='pin'),
    path('transactions/', TransactionsView.as_view(), name='transactions'),
    path('callback/', FlutterwaveCallbackView.as_view(), name='callback')
]
