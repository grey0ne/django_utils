from django.http import HttpRequest, HttpResponse
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sessions.backends.base import UpdateError
from django.contrib.sessions.exceptions import SessionInterrupted
from django.utils.http import http_date
from typing import Callable, Any
import time
import json
import base64
from asgiref.sync import async_to_sync

try:
    from users.frontend_user_data import get_user_data
except ImportError:
    get_user_data = None


class DomainRoutingMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        host = request.get_host().split(':')[0].lower()

        if host in settings.EXTRA_DOMAINS:
            # If host in extra domains, use custom urls
            request.urlconf = 'application.extra_urls' # type: ignore

        return self.get_response(request)


class JwtSessionMiddleware(SessionMiddleware):
    """
    Redefined middleware to add separate user data cookie acessible from javascript
    It allows to access user data without extra requests to the server
    get_user_data function is defined in users/frontend_user_data.py 
    """
    def get_user_data_for_frontend(self, request: HttpRequest) -> dict[str, Any] | None:
        if get_user_data is None:
            return {}
        return async_to_sync(get_user_data)(request)

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        result = super().process_response(request, response)
        try:
            modified = request.session.modified
            empty = request.session.is_empty()
        except AttributeError:
            return response
 
        cookie_name = settings.USER_DATA_COOKIE_NAME
        if cookie_name is not None and cookie_name in request.COOKIES and empty:
            response.delete_cookie(cookie_name)
        else:
            if modified and not empty and get_user_data is not None:
                if request.session.get_expire_at_browser_close():
                    max_age = None
                    expires = None
                else:
                    max_age = request.session.get_expiry_age()
                    expires_time = time.time() + max_age
                    expires = http_date(expires_time)
                # Save the session data and refresh the client cookie.
                # Skip session save for 5xx responses.
                if response.status_code < 500:
                    try:
                        request.session.save()
                    except UpdateError:
                        raise SessionInterrupted(
                            "The request's session was deleted before the "
                            "request completed. The user may have logged "
                            "out in a concurrent request, for example."
                        )
                    # base64 only to hide data in from casual user, it obviosly doesn't add security
                    # This is used only on the client side for speeding things up, for server side we use signed session token
                    user_data = self.get_user_data_for_frontend(request)
                    if user_data is not None:
                        data = json.dumps(user_data).encode('utf-8')
                        data = base64.b64encode(data).decode('ascii')
                        
                        response.set_cookie(
                            cookie_name,
                            data,
                            max_age=max_age,
                            expires=expires,
                            domain=settings.SESSION_COOKIE_DOMAIN,
                            path=settings.SESSION_COOKIE_PATH,
                            secure=True,
                            httponly=False,
                            samesite="Strict",
                        )
        return result