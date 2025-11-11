from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import CallSession, Participant
from .serializers import CallSessionSerializer
from django.contrib.auth import get_user_model
from agora_token_builder import RtcTokenBuilder, RtmTokenBuilder
import time
import uuid

User = get_user_model()

class GenerateTokenView(APIView):
    """Generate an Agora RTC (and optionally RTM) token for joining a channel.
    Request JSON:
    {
    "channel_name": "string",
    "account": "optional string user account",
    "uid": optional int,
    "role": "publisher" | "audience" (defaults to publisher)
    }
    Response: {"rtc_token": "...", "rtm_token": "... (optional)", "expires_at": unix_ts}
    """
    permission_classes = [permissions.AllowAny]


    def post(self, request):
        app_id = settings.AGORA_APP_ID
        app_cert = settings.AGORA_APP_CERTIFICATE
        if not app_id or not app_cert:
            return Response({'detail': 'Agora credentials are not configured on the server.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        channel_name = request.data.get('channel_name')
        account = request.data.get('account')
        uid = request.data.get('uid')
        role_str = request.data.get('role', 'publisher')
        role = 1 if role_str == 'publisher' else 2 # Role_Publisher=1, Role_Subscriber=2 (per token builder)


        if not channel_name:
            return Response({'detail': 'channel_name is required'}, status=status.HTTP_400_BAD_REQUEST)


        privilege_ts = int(time.time()) + int(getattr(settings, 'AGORA_TOKEN_EXPIRE_SECONDS', 600))


        # Build RTC token
        try:
            if account:
                rtc_token = RtcTokenBuilder.buildTokenWithAccount(app_id, app_cert, channel_name, account, role, privilege_ts)
            else:
                # pass uid as int; if none provided, generate a random one in safe range
                if uid is None:
                    uid = int(uuid.uuid4().int & (2**31-1)) # safe 32-bit int
                rtc_token = RtcTokenBuilder.buildTokenWithUid(app_id, app_cert, channel_name, int(uid), role, privilege_ts)
        except Exception as e:
            return Response({'detail': f'Failed to build token: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Optionally build RTM token (useful for signaling via Agora RTM)
        rtm_token = None
        try:
        # RTM token expects user account (string). Use account if provided, otherwise the current user id string.
            rtm_account = account or str(request.user.id)
            rtm_token = RtmTokenBuilder.buildToken(app_id, app_cert, rtm_account, 1, privilege_ts)
        except Exception:
        # RTM token is optional — don't fail the whole request if it errors
            rtm_token = None


        return Response({'rtc_token': rtc_token, 'rtm_token': rtm_token, 'expires_at': privilege_ts, 'uid': uid})

class StartCallView(APIView):
    """Create a CallSession and return channel + token for the host. Optionally notify callee via push/RTM.
    Request JSON: {"callee_id": int, "metadata": {...}}
    """
    permission_classes = [permissions.AllowAny]


    def post(self, request):
        callee_id = request.data.get('callee_id')
        metadata = request.data.get('metadata', {})
        # create unique channel name — use UUID to avoid collisions and leakage of predictable names
        channel_name = f"call_{uuid.uuid4().hex}"


        session = CallSession.objects.create(channel_name=channel_name, host=User.objects.get(id=1), metadata=metadata)


        # optionally create participant record for host
        p = Participant.objects.create(session=session, user=User.objects.get(id=1))


        # generate token for host to join immediately
        token_resp = GenerateTokenView().post(request._request.__class__.__mro__[0]) if False else None
        # we won't call GenerateTokenView directly; instead, reuse logic here quickly
        import time
        privilege_ts = int(time.time()) + int(getattr(settings, 'AGORA_TOKEN_EXPIRE_SECONDS', 600))
        try:
            uid = int(uuid.uuid4().int & (2**31-1))
            rtc_token = RtcTokenBuilder.buildTokenWithUid(settings.AGORA_APP_ID, settings.AGORA_APP_CERTIFICATE, channel_name, uid, 1, privilege_ts)
            rtm_account = str(request.user.id)
            rtm_token = RtmTokenBuilder.buildToken(settings.AGORA_APP_ID, settings.AGORA_APP_CERTIFICATE, rtm_account, 1, privilege_ts)
        except Exception as e:
            session.delete()
            return Response({'detail': 'Failed to build token for host', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        # TODO: push notification / send RTM message to callee to alert them to join.
        # Keep this backend-agnostic: integrate with your push service or an RTM server.


        return Response({'session_id': session.id, 'channel_name': channel_name, 'rtc_token': rtc_token, 'rtm_token': rtm_token, 'uid': uid, 'expires_at': privilege_ts}, status=status.HTTP_201_CREATED)

class EndCallView(APIView):
    permission_classes = [permissions.AllowAny]


    def post(self, request):
        session_id = request.data.get('session_id')
        session = get_object_or_404(CallSession, id=session_id)
        # optional permission: only host or admin can end
        if session.host != User.objects.get(id=1) and not request.user.is_staff:
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
        session.mark_ended()
        return Response({'detail': 'ended'})