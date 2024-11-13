from ninja.security.apikey import APIKeyCookie
from django.http import HttpRequest
from django.conf import settings
from dataorm.types import AuthData
from users.models import User
from typing import Any

async def async_get_user(request: HttpRequest) -> User:
    return await request.auser() #type: ignore auser is async property added in latest django versions

class AsyncSessionAuth(APIKeyCookie):

    param_name: str = settings.SESSION_COOKIE_NAME

    async def get_auth_data(self, request_user: User, request: HttpRequest) -> Any:
        return AuthData(user_id=request_user.id)


    async def authenticate(self, request: HttpRequest, key: str | None) -> Any:
        user = await async_get_user(request)
        if user.is_authenticated:
            return await self.get_auth_data(request_user=user, request=request)

        return None


django_auth = AsyncSessionAuth()

