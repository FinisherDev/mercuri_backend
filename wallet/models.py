import random
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
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=10, unique=True, blank=True)
    balance = models.FloatField(default=0.00)
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
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=[('credit', 'Credit'), ('debit', 'Debit')])
    transaction_format = models.CharField(max_length=10, choices=[('deposit', 'Deposit'), ('transfer', 'Transfer')])
    #status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('failed', 'Failed'), ('completed', 'Completed')])
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    creation_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.transaction_type.capitalize()} of ₦{self.amount} on {self.creation_date}"

    class Meta:
        indexes = [
            Index(fields= ['wallet', ])
        ]