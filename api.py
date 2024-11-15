from typing import Any, Callable, Type
from django.db import models
from ninja import Router
from ninja.pagination import paginate # type: ignore paginate does not support typing
from dataorm.auth import django_auth
from dataorm.queries import typed_data_list
from dataorm.pagination import PaginationBase, IDPagination, DateIDPagination
from dataorm.types import (
    Error, TransformSingleFunc, Decorator, SingleItemResponse, TransformListFunc, 
)


def get_response(response_type: type) -> dict[int, type]:
    return {200: response_type, 401: Error, 400: Error, 404: Error}


async def get_single_item_or_404(
    qset: models.QuerySet[Any],
    response_type: Type[SingleItemResponse],
    transform: TransformSingleFunc | None = None,
) -> SingleItemResponse | tuple[int, dict[str, str]]:
    if transform is not None:
        return transform(qset)
    result = await typed_data_list(qset, response_type)
    if len(result) == 0:
        return 404, {'detail': 'Not found'}
    return result[0]


def single_item(
    router: Router,
    url: str,
    response_type: Type[SingleItemResponse],
    auth: Any = django_auth,
) -> Decorator:
    def decorator(func: Callable[..., models.QuerySet[Any]]) -> Callable[..., Any]:
        router_decorator: Decorator = router.get(
            url, response=get_response(response_type), auth=auth
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
) -> Decorator:
    def decorator(func: Callable[..., models.QuerySet[Any]]) -> Callable[..., Any]:
        router_decorator: Decorator = router.get(
            url, response=get_response(list[response_type]), auth=auth
        )
        pagination_decorator: Any = paginate(
            pagination,
            response_type=response_type,
            date_field=date_field,
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
) -> Decorator:
    return api_list(
        router=router,
        url=url,
        pagination=DateIDPagination,
        response_type=response_type,
        date_field=date_field,
        auth=auth,
        transform=transform,
    )
