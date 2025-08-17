import jwt
import datetime
from django.conf import settings
from typing import TypedDict, Any, Literal


class JwtPayload(TypedDict):
    user_id: int
    username: str
    exp: datetime.datetime
    type: Literal["access"] | Literal["refresh"]


def create_access_token(user_id: int, username: str) -> str:
    payload: dict[str, Any] = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=settings.JWT_ACCESS_EXP_DELTA_SECONDS),
        "type": "access"
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


def create_refresh_token(user_id: int) -> str:

    payload: dict[str, Any] = {
        "user_id": user_id,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=settings.JWT_REFRESH_EXP_DELTA_SECONDS),
        "type": "refresh"
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


def decode_jwt_token(token: str, expected_type: Literal["access"] | Literal["refresh"]) -> JwtPayload | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload["type"] != expected_type:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None   # token is expired
    except jwt.InvalidTokenError:
        return None   # token is invalid