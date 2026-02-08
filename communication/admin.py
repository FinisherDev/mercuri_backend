from django.contrib import admin
from .models import Call, ChatRoom, Message

# Register your models here.

admin.site.register(Call)
admin.site.register(ChatRoom)
admin.site.register(Message)