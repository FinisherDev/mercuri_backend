from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from urllib.parse import parse_qs

@database_sync_to_async
def get_user_from_token(token_string):
    try:
        access_token = AccessToken(token_string)
        print ("Access token", access_token)
        user_id = access_token['user_id']
        print(f"The User ID {user_id}")

        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.get(id=user_id)
    except Exception as e:
        print(f"Token validation failed: {e}")
        return AnonymousUser

class TokenAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        print(f"The query stirng {query_string}")
        query_params = parse_qs(query_string)
        print(f"Qurey params {query_params}")
        token = query_params.get('token', [None])[0]
        print(f'The bloody token {token}')

        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            print("So switching")
            scope['user'] = AnonymousUser
        return await self.app(scope, receive, send)