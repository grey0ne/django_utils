from dataclasses import dataclass
from django.db import models
from typing import TypeVar, Protocol, ClassVar, Any, Callable, Sequence, Annotated, TypedDict, Coroutine

TransformListFunc = Callable[[models.QuerySet[Any]], Coroutine[Any, Any, Sequence[Any]]]
TransformSingleFunc = Callable[[models.QuerySet[Any]], Coroutine[Any, Any, Any]]

IdType = int
FieldName = str

class DataclassProtocol(Protocol):
    # checking for this attribute is currently
    # the most reliable way to ascertain that something is a dataclass
    __dataclass_fields__: ClassVar[dict[str, Any]]

@dataclass(kw_only=True, slots=True, frozen=True)
class ModelProtocol:
    id: IdType

SingleItemResponse = TypeVar('SingleItemResponse', bound=DataclassProtocol)
ResultType = TypeVar('ResultType', bound=ModelProtocol)

ResultKey = str | int

@dataclass(kw_only=True, slots=True, frozen=True)
class JsonSchema:
    pass

T = TypeVar('T')

NestedDict = dict[ResultKey, dict[ResultKey, T]]
FlatDict = dict[ResultKey, T]

NestedOrFlatDict = NestedDict[T] | FlatDict[T]
ResultType = TypeVar("ResultType", bound=DataclassProtocol)

URLAnnotation = 'URLAnnotation'
URLSchema = Annotated[str, URLAnnotation]

ExternalAnnotation = 'ExternalField'
ExternalField = Annotated[T, ExternalAnnotation]

@dataclass(kw_only=True, slots=True, frozen=True)
class Error:
    detail: str

@dataclass(kw_only=True, slots=True, frozen=True)
class EmptyResponse:
    detail: str = ''

Decorator = Callable[[Callable[..., Any]], Callable[..., Any]]

@dataclass(kw_only=True, slots=True, frozen=True)
class AuthData:
    user_id: IdType


Base64FileAnnotation = 'Base64FILE'
Base64File = Annotated[str, Base64FileAnnotation]

@dataclass(kw_only=True, slots=True, frozen=True)
class FileUploadData:
    uploaded_file: Base64File
    file_name: str


LocalizedStringSchema = TypedDict('LocalizedStringSchema', {
    'ru': str,
    'de': str,
    'en': str,
    'es': str,
    'pt': str
}, total=False)


@dataclass(kw_only=True, slots=True, frozen=True)
class LoginRequestData:
    username: str
    password: str

@dataclass(kw_only=True, slots=True, frozen=True)
class TranslationRequestData:
    locale: str
    text: str

@dataclass(kw_only=True, slots=True, frozen=True)
class TranslationResponseData:
    translation: str