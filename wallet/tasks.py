from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Wallet, Transaction
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


