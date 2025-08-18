from ninja import Router, Body
from ninja.errors import HttpError
from django.http import HttpRequest, HttpResponse
from django.conf import settings
from django.contrib.auth import aauthenticate
from users.models import User
from django_utils.api import action
from django_utils.jwt import create_access_token, decode_jwt_token
from django_utils.schema import LoginRequestData, EmptyResponse
from django_utils.constants import ACCESS_TOKEN_COOKIE_NAME, REFRESH_TOKEN_COOKIE_NAME

auth_router = Router()

async def authenticate_user(request: HttpRequest, username: str, password: str) -> User:
    """
    This function is needed because django auth returns AbstractBaseUser and type checking fails
    """
    auth_user = await aauthenticate(request, username=username, password=password)
    if not auth_user:
        raise HttpError(401, "Invalid credentials")
    return auth_user # type: ignore


def set_access_token_cookie(response: HttpResponse, access_token: str):
    response.set_cookie(
        ACCESS_TOKEN_COOKIE_NAME, access_token,
        httponly=True, secure=True, samesite="Strict",
        max_age=settings.JWT_ACCESS_EXP_DELTA_SECONDS
    )


@action(auth_router, url='/login', response_type=EmptyResponse, auth=None)
async def login_endpoint(request: HttpRequest, data: Body[LoginRequestData], response: HttpResponse):
    user = await authenticate_user(request, data.username, data.password)
    
    access_token = create_access_token(user.id, user.username)

    set_access_token_cookie(response, access_token)

    return EmptyResponse()


@action(auth_router, url='/refresh_access_token', response_type=EmptyResponse, auth=None)
async def refresh_access_token_endpoint(request: HttpRequest, response: HttpResponse):
    refresh_token = request.COOKIES.get(REFRESH_TOKEN_COOKIE_NAME)
    if not refresh_token:
        raise HttpError(401, "No refresh token")

    payload = decode_jwt_token(refresh_token, expected_type="refresh")
    if not payload:
        raise HttpError(401, "Invalid or expired refresh token")

    try:
        user = User.objects.get(id=payload["user_id"])
    except User.DoesNotExist:
        raise HttpError(401, "User not found")

    new_access_token = create_access_token(user.id, user.username)

    set_access_token_cookie(response, new_access_token)

    return EmptyResponse()
