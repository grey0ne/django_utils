from ninja.pagination import PaginationBase
from typing import Any, Type, Sequence
from dataorm.schema import DataclassProtocol, TransformListFunc, ModelProtocol
from dataorm.queries import typed_data_list
from datetime import datetime
from django.db import models
from django.db.models import Q


DEFAULT_PER_PAGE = 30

class EfficientPagination[ResultType: DataclassProtocol](PaginationBase):
    def __init__(
        self,
        *,
        response_type: Type[ResultType],
        transform: TransformListFunc | None = None,
        **kwargs: Any,
    ) -> None:
        self.response_type = response_type
        self.transform = transform
        super().__init__(**kwargs)

    def paginate_queryset(self, queryset: models.QuerySet[Any], pagination: Any, **params: Any) -> Any:
        raise NotImplementedError('Syncronous pagination is not supported in this project. apaginate_queryset should be implemented.')

    async def transform_queryset(
        self, queryset: models.QuerySet[Any]
    ):
        if self.transform is not None:
            return await self.transform(queryset)
        return await typed_data_list(queryset, self.response_type)


class IDPagination[ResultType: ModelProtocol](EfficientPagination[ResultType]):

    class Input(PaginationBase.Input):
        """
        Pagination is reversed, from recent ot older records, hence the field names
        """
        to_id: int | None = None
        per_page: int = DEFAULT_PER_PAGE

    class Output(PaginationBase.Output):
        items: list[ResultType]
        last_id: int | None

    def get_result(self, result: Sequence[ResultType]) -> dict[str, Any]:
        result_data: dict[str, Any] = {
            'items': result,
            'last_id': result[-1].id if result else None,
            'count': len(result),
        }
        return result_data

    async def apaginate_queryset(
        self, queryset: models.QuerySet[Any], pagination: Input, **params: Any
    ) -> dict[str, Any]:
        if pagination.to_id is not None:
            queryset = queryset.filter(id__lt=pagination.to_id)
        result_qset = queryset.order_by('-id')[: pagination.per_page]
        result = await self.transform_queryset(result_qset)
        return self.get_result(result)


class DateIDPagination[ResultType: ModelProtocol](EfficientPagination[ResultType]):

    def __init__(self, *, date_field: str, reverse_order: bool=False, **kwargs: Any) -> None:
        self.date_field = date_field
        self.reverse_order = reverse_order
        super().__init__(**kwargs)

    class Input(PaginationBase.Input):
        """
        Pagination is reversed, from recent ot older records, hence the field names
        """
        to_timestamp: int | None = None
        to_id: int | None = None
        per_page: int = DEFAULT_PER_PAGE

    class Output(PaginationBase.Output):
        items: list[ResultType]
        last_id: int | None
        last_timestamp: int | None

    def get_timestamp(self, item: ResultType) -> int:
        result = int(getattr(item, self.date_field).timestamp() * 1000000)
        return result

    def filter_to_timestamp(self, qset: models.QuerySet[Any], pagination: Input) -> models.QuerySet[Any]:
        if pagination.to_timestamp is not None:
            ms = pagination.to_timestamp # timestamp in microseconds
            to_date = datetime.fromtimestamp(ms//1000000).replace(microsecond=ms%1000000) # to avoid floating point conversion
            if self.reverse_order:
                date_filter = Q(**{f'{self.date_field}__gt': to_date})
                id_filter = Q(
                    id__gt=pagination.to_id,
                    **{f'{self.date_field}': to_date},
                )
            else:
                date_filter = Q(**{f'{self.date_field}__lt': to_date})
                id_filter = Q(
                    id__lt=pagination.to_id,
                    **{f'{self.date_field}': to_date},
                )
            qset = qset.filter(date_filter | id_filter)

        if self.reverse_order:
            qset = qset.order_by(f'{self.date_field}', 'id')[:pagination.per_page]
        else:
            qset = qset.order_by(f'-{self.date_field}', '-id')[:pagination.per_page]
        return qset

    def get_result(self, result: Sequence[ResultType]) -> dict[str, Any]:
        last_elem = result[-1] if len(result) > 0 else None
        return {
            'items': result,
            'count': len(result),
            'last_id': last_elem.id if last_elem else None,
            'last_timestamp': self.get_timestamp(last_elem) if last_elem else None,
        }

    async def apaginate_queryset(
        self, queryset: models.QuerySet[Any], pagination: Input, **params: Any
    ) -> dict[str, Any]:
        queryset = self.filter_to_timestamp(queryset, pagination)
        result = await self.transform_queryset(queryset)
        return self.get_result(result)

