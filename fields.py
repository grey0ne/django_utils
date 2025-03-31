from typing import Any, get_args, get_origin
from django.db import models
from dataorm.types import (
    JsonSchema, URLAnnotation, Base64FileAnnotation, ExternalAnnotation
)

def LocalizedStringField(verbose_name: str):
    return models.JSONField[dict[str, str]](
        null=True, blank=True, verbose_name=verbose_name
    )

def is_json_schema_dict(field_type: Any) -> bool:
    type_args = get_args(field_type)
    return get_origin(field_type) == dict and issubclass(type_args[1], JsonSchema)

def is_json_schema_list(field_type: Any) -> bool:
    type_args = get_args(field_type)
    return get_origin(field_type) == list and issubclass(type_args[0], JsonSchema)

def remove_optional_from_type(field_type: Any) -> Any:
    args = get_args(field_type)
    if len(args) == 2 and args[1] == type(None):
        return args[0]
    return field_type

def is_json_schema(field_type: Any) -> bool:
    type_args = get_args(field_type)
    return len(type_args) == 0 and issubclass(field_type, JsonSchema)

def is_url_field(field_type: Any) -> bool:
    if hasattr(field_type, '__metadata__'):
        return field_type.__metadata__[0] == URLAnnotation
    return False

def is_external_field(field_type: Any) -> bool:
    """
        This used for fields that are not in the model and calculated separately
    """
    if hasattr(field_type, '__metadata__'):
        return field_type.__metadata__[0] == ExternalAnnotation
    return False

def is_file_field(field_type: Any) -> bool:
    if hasattr(field_type, '__metadata__'):
        return field_type.__metadata__[0] == Base64FileAnnotation
    return False

