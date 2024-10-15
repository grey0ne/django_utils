from dataclasses import dataclass
from django.db import models
from typing import TypeVar, Protocol, ClassVar, Any, Callable, Sequence

TransformListFunc = Callable[[models.QuerySet[Any]], Sequence[Any]]
TransformSingleFunc = Callable[[models.QuerySet[Any]], Any]

IdType = int

class DataclassProtocol(Protocol):
    # checking for this attribute is currently
    # the most reliable way to ascertain that something is a dataclass
    __dataclass_fields__: ClassVar[dict[str, Any]]

SingleItemResponse = TypeVar('SingleItemResponse', bound=DataclassProtocol)

ResultKey = str | int

@dataclass(kw_only=True, slots=True, frozen=True)
class JsonSchema:
    pass

T = TypeVar('T')

NestedDict = dict[ResultKey, dict[ResultKey, T]]
FlatDict = dict[ResultKey, T]

NestedOrFlatDict = NestedDict[T] | FlatDict[T]

URLAnnotation = 'URLAnnotation'

@dataclass(kw_only=True, slots=True, frozen=True)
class Error:
    detail: str

Decorator = Callable[[Callable[..., Any]], Callable[..., Any]]

@dataclass(kw_only=True, slots=True, frozen=True)
class AuthData:
    user_id: IdType