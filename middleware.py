from django.http import HttpRequest, HttpResponse
from django.conf import settings

from typing import Callable

class DomainRoutingMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        host = request.get_host().split(':')[0].lower()

        if host in settings.EXTRA_DOMAINS:
            # If host in extra domains, use custom urls
            request.urlconf = 'application.extra_urls' # type: ignore

        return self.get_response(request)