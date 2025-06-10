from ninja.security.apikey import APIKeyCookie
from django.http import HttpRequest
from django.conf import settings
from django.contrib.auth import SESSION_KEY
from dataorm.schema import AuthData
from users.models import User
from typing import Any

class UserNotAuthenticatedError(Exception):
    """Custom exception for unauthenticated user access."""
    pass


async def async_get_user(request: HttpRequest) -> User:
    user_pk = User._meta.pk
    if user_pk is None:
        raise ValueError("User model does not have a primary key defined.")
    if SESSION_KEY not in request.session:
        raise UserNotAuthenticatedError("User is not authenticated.")
    user_id = user_pk.to_python(request.session[SESSION_KEY])
    return await User.objects.aget(pk=user_id)

class AsyncSessionAuth(APIKeyCookie):

    param_name: str = settings.SESSION_COOKIE_NAME

    async def get_auth_data(self, request_user: User, request: HttpRequest) -> Any:
        return AuthData(user_id=request_user.id)


    async def authenticate(self, request: HttpRequest, key: str | None) -> Any:
        try:
            user = await async_get_user(request)
        except UserNotAuthenticatedError:
            return None
        return await self.get_auth_data(request_user=user, request=request)


django_auth = AsyncSessionAuth()

