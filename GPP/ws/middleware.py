from urllib.parse import parse_qs

from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async

from rest_framework_simplejwt.authentication import JWTAuthentication, AuthUser
from rest_framework_simplejwt.tokens import Token

from django.db import close_old_connections
from django.core import exceptions

class SimpleJWTAuthMiddleware(BaseMiddleware):
    """
    Custom Simple JWT auth midddleware for WebSocket
    """

    jwt_authenticator = JWTAuthentication()

    @database_sync_to_async
    def get_user(self, validated_token: Token) -> AuthUser:
        """
        Attempts to find and return a user using the given validated token.(Async)
        """
        return self.jwt_authenticator.get_user(validated_token)

    async def __call__(self, scope, receive, send):
        # Parse le token depuis la query string
        query_string = parse_qs(scope['query_string'].decode())
        
        token = None
        if 'token' in query_string:
            token = query_string['token'][0]

        if token:
            try:
                validated_token = self.jwt_authenticator.get_validated_token(token)
                user = await self.get_user(validated_token)
                scope['user'] = user
            except Exception as e:
                raise e
        else:
            raise exceptions.BadRequest("token parameter required.")

        close_old_connections() # Fermer la connexion à la DB
        return await super().__call__(scope, receive, send)
