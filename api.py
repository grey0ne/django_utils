from typing import Any, Callable, Type
from django.db import models
from ninja import Router
from ninja.pagination import paginate # type: ignore paginate does not support typing
from ninja.errors import HttpError
from django_utils.auth import django_auth
from django_utils.queries import typed_data_list
from django_utils.pagination import PaginationBase, IDPagination, DateIDPagination
from django_utils.schema import (
    Error, TransformSingleFunc, Decorator, SingleItemResponse, TransformListFunc, DataclassProtocol
)


def get_response(response_type: type) -> dict[int, type]:
    return {200: response_type, 401: Error, 400: Error, 404: Error}


async def get_single_item_or_404(
    qset: models.QuerySet[Any],
    response_type: Type[SingleItemResponse],
    transform: TransformSingleFunc | None = None,
) -> SingleItemResponse:
    if transform is not None:
        qset = await transform(qset)
    result = await typed_data_list(qset, response_type)
    if len(result) == 0:
        raise HttpError(404, 'Not found')
    if len(result) > 1:
        raise HttpError(400, 'More than one item found')
    return result[0]


def action(
    router: Router,
    url: str,
    response_type: Type[DataclassProtocol],
    auth: Any = django_auth,
 ) -> Decorator:
    def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        router_decorator: Decorator = router.post(
            url, response=get_response(response_type), auth=auth
        )
        return router_decorator(func)
    return wrapper


def single_item(
    router: Router,
    url: str,
    response_type: Type[SingleItemResponse],
    auth: Any = django_auth,
) -> Decorator:
    def wrapper(func: Callable[..., models.QuerySet[Any]]) -> Callable[..., Any]:
        router_decorator: Decorator = router.get(
            url, response=get_response(response_type), auth=auth
        )
        return router_decorator(func)

    return wrapper


def unpaginated_list(
    router: Router,
    url: str,
    response_type: Type[SingleItemResponse],
    auth: Any = django_auth,
    transform: TransformListFunc | None = None,
) -> Decorator:
    def decorator(func: Callable[..., models.QuerySet[Any]]) -> Callable[..., Any]:
        router_decorator: Decorator = router.get(
            url, response=get_response(list[response_type]), auth=auth
        )
        return router_decorator(func)
    return decorator


def api_list(
    router: Router,
    url: str,
    pagination: Type[PaginationBase],
    response_type: Type[SingleItemResponse],
    auth: Any = django_auth,
    date_field: str | None = None,
    transform: TransformListFunc | None = None,
    reverse_order: bool = False,
) -> Decorator:
    def decorator(func: Callable[..., models.QuerySet[Any]]) -> Callable[..., Any]:
        router_decorator: Decorator = router.get(
            url, response=get_response(list[response_type]), auth=auth
        )
        pagination_decorator: Any = paginate( # type: ignore paginate does not support typing properly
            pagination,
            response_type=response_type,
            date_field=date_field,
            reverse_order=reverse_order,
            transform=transform,
        )
        return router_decorator(pagination_decorator(func))

    return decorator


def id_paginated(
    router: Router,
    url: str,
    response_type: Type[SingleItemResponse],
    auth: Any = django_auth,
    transform: TransformListFunc | None = None,
) -> Decorator:
    return api_list(
        router=router,
        url=url,
        pagination=IDPagination,
        auth=auth,
        response_type=response_type,
        transform=transform,
    )


def date_paginated(
    router: Router,
    url: str,
    response_type: Type[SingleItemResponse],
    auth: Any = django_auth,
    date_field: str = 'created_at',
    transform: TransformListFunc | None = None,
    reverse_order: bool = False,
) -> Decorator:
    return api_list(
        router=router,
        url=url,
        pagination=DateIDPagination,
        response_type=response_type,
        date_field=date_field,
        reverse_order=reverse_order,
        auth=auth,
        transform=transform,
    )
