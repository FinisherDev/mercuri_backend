import random, uuid
from django.db import models
from django.db.models import Index
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password

# Create your models here.

def generate_unique_account_number():
    while True:
        number = "582" + str(random.randint(1000000, 9999999))
        if not Wallet.objects.filter(account_number=number).exists():
            return number

class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default = 1)
    account_number = models.CharField(max_length=10, unique=True, blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    transfer_pin = models.CharField(max_length=4, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.first_name}'s Wallet"

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = generate_unique_account_number()
        super().save(*args, **kwargs)
    
    def deposit(self, amount):
        self.balance += amount
        self.save()

    def transfer(self, amount, recipient_wallet):
        if self.balance >= amount:
            self.balance -= amount
            recipient_wallet.balance += amount
            self.save()
            recipient_wallet.save()
            return True
        else:
            return False

    def set_transfer_pin(self, raw_pin):
        self.transfer_pin = make_password(raw_pin)

    def check_transfer_pin(self, raw_pin):
        return check_password(raw_pin, self.transfer_pin)

    class Meta:
        indexes = [
            Index(fields= ['user', 'account_number',]),
        ]
    
class Transaction(models.Model):
    FORMAT_CHOICES = [
        ('deposit', 'Deposit'), 
        ('transfer', 'Transfer'), 
        ('withdrawal', 'Withdrawal'), 
        ('reserve', 'Reserve'), 
        ('release', 'Release')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=[('credit', 'Credit'), ('debit', 'Debit')])
    transaction_format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    #status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('failed', 'Failed'), ('completed', 'Completed')])
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    creation_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.transaction_format.capitalize()} Transaction of ₦{self.amount} on {self.creation_date}"

    class Meta:
        indexes = [
            Index(fields= ['wallet', ])
        ]

class WithdrawalRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'PENDING'),
        ('processing', 'PROCESSING'),
        ('completed', 'COMPLETED'),
        ('failed', 'FAILED'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="withdrawals")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    bank_account_name = models.CharField(max_length=255)
    bank_account_number = models.CharField(max_length=12)
    bank_code = models.CharField(max_length=32)
    status = models.CharField(max_length = 30 ,choices = STATUS_CHOICES, default = 'pending')
    faliure_reason = models.TextField(blank = True, null = True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        indexes = [
            Index(fields = ['status', 'wallet', 'created_at']),
        ]