from functools import partial
from typing import Any

from django.http import HttpRequest, HttpResponse
from ninja import NinjaAPI
from ninja.errors import HttpError


class ApiError(HttpError):
    """
    An error shown to the user. The response is {"code", "detail", "params"}:
    `code` is a stable key the frontend translates (next_utils useFormatApiError, ApiErrors.<code>),
    `detail` is the English text for logs and other API clients, `params` are substituted into the translation
    """

    def __init__(self, status_code: int, code: str, message: str = '', **params: Any) -> None:
        super().__init__(status_code, message or code)
        self.code = code
        self.params = params


def _api_error_response(request: HttpRequest, exc: ApiError, api: NinjaAPI) -> HttpResponse:
    data = {'code': exc.code, 'detail': exc.message, 'params': exc.params}
    return api.create_response(request, data, status=exc.status_code)


def add_api_error_handler(api: NinjaAPI) -> None:
    """Without the handler ninja answers an ApiError like any HttpError, with `detail` only"""
    api.add_exception_handler(ApiError, partial(_api_error_response, api=api))
