from ninja.security.apikey import APIKeyCookie
from django.http import HttpRequest
from django.conf import settings
from django.contrib.auth import SESSION_KEY
from users.models import User
from typing import Any
from django_utils.schema import AuthData
from django_utils.jwt import decode_jwt_token
from django_utils.constants import ACCESS_TOKEN_COOKIE_NAME

class UserNotAuthenticatedError(Exception):
    """Custom exception for unauthenticated user access."""
    pass


def get_user_id_from_session(request: HttpRequest) -> int | None:
    user_pk = User._meta.pk # type: ignore
    if user_pk is None: # type: ignore
        raise ValueError("User model does not have a primary key defined.")
    if SESSION_KEY not in request.session:
        return None
    return user_pk.to_python(request.session[SESSION_KEY])


def get_user_id_from_jwt(request: HttpRequest) -> int | None:
    access_token = request.COOKIES.get(ACCESS_TOKEN_COOKIE_NAME)
    if access_token is None:
        return None
    payload = decode_jwt_token(access_token, expected_type="access")
    if payload is None:
        return None
    return payload["user_id"]


def get_user_id_from_request(request: HttpRequest) -> int | None:
    if settings.JWT_ENABLED:
        return get_user_id_from_jwt(request)
    return get_user_id_from_session(request)


async def async_get_user(request: HttpRequest) -> User:
    user_id = get_user_id_from_request(request)
    if user_id is None:
        raise UserNotAuthenticatedError("User is not authenticated.")
    return await User.objects.aget(pk=user_id)


async def async_get_user_or_none(request: HttpRequest) -> User | None:
    user_id = get_user_id_from_request(request)
    if user_id is None:
        return None
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


class JwtAuth(APIKeyCookie):
    param_name: str = ACCESS_TOKEN_COOKIE_NAME

    def authenticate(self, request: HttpRequest, key: str | None) -> Any:
        if key is None:
            return None
        payload = decode_jwt_token(key, expected_type="access")
        if payload is None:
            return None
        return AuthData(user_id=payload["user_id"])


jwt_auth = JwtAuth()