import os
import time
from django.conf import settings

# import token builder from package
try:
    from agora_token_builder import RtcTokenBuilder, RtcRole
except Exception as exc:
    raise ImportError("install agora_token_builder or correct package namessssss") from exc

def build_token_with_user_account(channel_name: str, user_account: str, expire_seconds: int = 600):
    """
    Use user account (string uid) tokens so we can pass string UIDs easily.
    """
    app_id = settings.AGORA_APP_ID
    app_cert = settings.AGORA_APP_CERTIFICATE
    current_ts = int(time.time())
    privilege_expired_ts = current_ts + expire_seconds
    token = RtcTokenBuilder.buildTokenWithUserAccount(app_id, app_cert, channel_name, user_account, RtcRole.PUBLISHER, privilege_expired_ts)
    return token
