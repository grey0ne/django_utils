from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from typing import TypedDict, Any, Literal
import jwt
import datetime


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


class SessionStore(SessionBase):
    def load(self) -> dict[str, Any]:
        """
        Load the data from the key itself instead of fetching from some
        external data store. Opposite of _get_session_key(), raise BadSignature
        if signature fails.
        """
        try:
            return jwt.decode(self.session_key or "", settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        except Exception:
            # BadSignature, ValueError, or unpickling exceptions. If any of
            # these happen, reset the session.
            self.create()
        return {}

    async def aload(self):
        return self.load()

    def create(self):
        self.modified = True

    async def acreate(self):
        return self.create()

    def save(self, must_create: bool = False):
        self._session_key = self._get_session_key()
        self.modified = True

    async def asave(self, must_create: bool = False):
        return self.save(must_create=must_create)

    def exists(self, session_key: str | None = None) -> bool:
        """
        This method makes sense when you're talking to a shared resource, but
        it doesn't matter when you're storing the information in the client's
        cookie.
        """
        return False

    async def aexists(self, session_key: str | None = None) -> bool:
        return self.exists(session_key=session_key)

    def delete(self, session_key: str | None = None):
        """
        To delete, clear the session key and the underlying data structure
        and set the modified flag so that the cookie is set on the client for
        the current request.
        """
        self._session_key = ""
        self._session_cache = {}
        self.modified = True

    async def adelete(self, session_key: str | None = None):
        return self.delete(session_key=session_key)

    def cycle_key(self):
        """
        Keep the same data but with a new key. Call save() and it will
        automatically save a cookie with a new key at the end of the request.
        """
        self.save()

    async def acycle_key(self):
        return self.cycle_key()

    def _get_session_data(self) -> dict[str, Any]:
        # method to make type checkers happy
        return self._session # type: ignore

    def _get_session_key(self) -> str:
        """
        Instead of generating a random string, generate a secure url-safe
        base64-encoded string of data as our session key.
        """
        session_data = self._get_session_data()
        return jwt.encode(session_data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @classmethod
    def clear_expired(cls):
        pass

    @classmethod
    async def aclear_expired(cls):
        pass