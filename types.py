from dataclasses import dataclass
from typing import TypeVar, Protocol, ClassVar, Any

class DataclassProtocol(Protocol):
    # checking for this attribute is currently
    # the most reliable way to ascertain that something is a dataclass
    __dataclass_fields__: ClassVar[dict[str, Any]]

ResultKey = str | int

@dataclass(kw_only=True, slots=True, frozen=True)
class JsonSchema:
    pass

T = TypeVar('T')

NestedDict = dict[ResultKey, dict[ResultKey, T]]
FlatDict = dict[ResultKey, T]

NestedOrFlatDict = NestedDict[T] | FlatDict[T]

URLAnnotation = 'URLAnnotation'