from collections import defaultdict
from dataclasses import fields, is_dataclass
from functools import reduce
from typing import Any, Sequence, Type, TypeVar, get_args, get_origin

from django.core.files.storage import default_storage
from django.db import models
from django.db.models import Q

from dataorm.types import (
    NestedDict, JsonSchema, FlatDict, ResultKey,
    DataclassProtocol, URLAnnotation, ResultType, FieldName
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


def dict_from_dataclass(obj: DataclassProtocol) -> dict[str, Any]:
    """
    Converts nested dataclass object to regular python dictionary
    Works recursively for nested dataclasses
    """
    kw: dict[str, Any] = {}
    if isinstance(obj, dict):
        return obj
    for field in fields(obj):
        field_type = remove_optional_from_type(field.type)
        field_data = getattr(obj, field.name)
        if field_data is None:
            continue
        elif is_json_schema_dict(field_type):
            kw[field.name] = {k: dict_from_dataclass(v) for k, v in field_data.items()}
        elif is_json_schema_list(field_type):
            kw[field.name] = [dict_from_dataclass(v) for v in field_data]
        elif is_json_schema(field_type):
            kw[field.name] = dict_from_dataclass(field_data)
        else:
            kw[field.name] = field_data
    return kw


def is_model_schema(field_type: type):
    return is_dataclass(field_type) and not issubclass(field_type, JsonSchema)


T = TypeVar('T', bound=models.Model)


async def bulk_create_wrapper(
    model: Type[T],
    objs_to_create: Sequence[T],
    unique_fields: list[str] = [],
    ignore_conflicts: bool = False,
    update_conflicts: bool = False,
    update_fields: list[str] = [],
    batch_size: int = 100,
) -> list[T]:
    # Wrapper is necessary for compatibility with different DB backends
    return await model.objects.abulk_create(
        objs_to_create,
        batch_size=batch_size,
        ignore_conflicts=ignore_conflicts,
        update_conflicts=update_conflicts, # type: ignore Error in stubs
        unique_fields=unique_fields,
        update_fields=update_fields,
    )


M = TypeVar('M', bound=models.Model)
R = TypeVar('R', bound=DataclassProtocol)


async def bulk_create_to_nested_dict(
    model: Type[M],
    objs_to_create: Sequence[M],
    result_type: Type[R],
    key_fields: tuple[str, str],
    unique_fields: list[str] = [],
    update_fields: list[str] = [],
) -> NestedDict[R]:
    """
    Shortcut for bulk creating objects and converting result to nested dictionary of dataclasses
    Key fields are used to create key on corresponding levels of nested dict
    """
    ignore_conflicts = len(update_fields) == 0
    result_models = await bulk_create_wrapper(
        model=model,
        objs_to_create=objs_to_create,
        update_conflicts=not ignore_conflicts,
        ignore_conflicts=ignore_conflicts,
        unique_fields=unique_fields,
        update_fields=update_fields,
    )
    result: NestedDict[R] = defaultdict[ResultKey, dict[ResultKey, R]](dict)
    for obj in result_models:
        key = getattr(obj, key_fields[0])
        sub_key = getattr(obj, key_fields[1])
        kw = {field.name: getattr(obj, field.name) for field in fields(result_type)}
        result_obj = get_obj_from_values(result_type, kw)
        result[key][sub_key] = result_obj
    return result


async def bulk_create_to_flat_dict(
    model: Type[M],
    objs_to_create: Sequence[M],
    result_type: Type[R],
    key_field: str,
    unique_fields: list[str] = [],
    update_fields: list[str] = [],
) -> FlatDict[R]:
    """
    Shortcut for bulk creating objects and converting result to flat dictionary of dataclasses
    """
    ignore_conflicts = len(update_fields) == 0
    result_models = await bulk_create_wrapper(
        model=model,
        objs_to_create=objs_to_create,
        update_conflicts=not ignore_conflicts,
        ignore_conflicts=ignore_conflicts,
        unique_fields=unique_fields,
        update_fields=update_fields,
    )
    result: FlatDict[R] = {}
    for obj in result_models:
        key = getattr(obj, key_field)
        kw = {field.name: getattr(obj, field.name) for field in fields(result_type)}
        result[key] = get_obj_from_values(result_type, kw)
    return result


async def bulk_create_to_list(
    model: Type[M],
    objs_to_create: Sequence[M],
    result_type: Type[R],
    unique_fields: list[str] = [],
    update_fields: list[str] = [],
) -> list[R]:
    ignore_conflicts = len(update_fields) == 0
    result_models = await bulk_create_wrapper(
        model=model,
        objs_to_create=objs_to_create,
        update_conflicts=not ignore_conflicts,
        ignore_conflicts=ignore_conflicts,
        unique_fields=unique_fields,
        update_fields=update_fields,
    )
    result: list[R] = []
    for obj in result_models:
        kw = {field.name: getattr(obj, field.name) for field in fields(result_type)}
        result.append(get_obj_from_values(result_type, kw))
    return result


def get_field_from_json(type_class: type, data: dict[str, Any] | None):
    """
    Converts plain dictionary to dataclass object
    Works recursively for nested dataclasses
    """
    if data is None:
        return None
    kw: dict[str, Any] = {}
    for field in fields(type_class):
        field_data = data.get(field.name)
        field_type = remove_optional_from_type(field.type)
        result = convert_field_to_json(field_data, field_type)
        if result is not None:
            kw[field.name] = result
    if len(kw) == 0:
        return None
    return type_class(**kw)

def convert_dict_to_json(data: dict[str, Any], type_class: type) -> dict[str, Any]:
    return { k: get_field_from_json(type_class, v) for k, v in data.items() }

def convert_list_to_json(data: list[Any], type_class: type) -> list[Any]:
    return [ get_field_from_json(type_class, v) for v in data ]

def convert_field_to_json(field_data: Any, field_type: Any) -> Any:
    """
    Converts nested dataclasses to plain dictionary for serialization
    """
    type_args = get_args(field_type)
    if field_data is None:
        return None
    elif is_json_schema_dict(field_type):
        return convert_dict_to_json(field_data, type_args[1])
    elif is_json_schema_list(field_type):
        return convert_list_to_json(field_data, type_args[0])
    elif is_json_schema(field_type):
        return get_field_from_json(field_type, field_data)
    elif is_url_field(field_type):
        return default_storage.url(field_data)
    else:
        return field_data

def get_obj_from_related_field(data: dict[str, Any], field_name: str, field_type: type):
    """
    Extracts nested dataclass from dictionary using Django double underscore notation 
    """
    prefix = f"{field_name}__"
    sub_data = {
        k.replace(prefix, '', 1): v
        for k, v in data.items()
        if k.startswith(prefix)
    }
    if 'id' in sub_data and sub_data['id'] is None:
        sub_obj = None
    else:
        sub_obj = get_obj_from_values(field_type, sub_data)
    return sub_obj


def get_obj_from_values(type_class: type, data: dict[str, Any], related_field: FieldName | None = None):
    """
    Converts django queryset values method result to dataclass object
    It recursively processes all nested dataclasses, unfolding their fields by double underscore
    """
    kw: dict[str, Any] = {}
    for field in fields(type_class):
        field_type = remove_optional_from_type(field.type)
        field_name = field.name if related_field is None else f"{related_field}__{field.name}"
        field_data = data.get(field_name)
        if is_model_schema(field_type):
            # Nested dataclass
            kw[field.name] = get_obj_from_related_field(data, field_name, field_type)
        else:
            result = convert_field_to_json(field_data, field_type)
            if result is not None:
                kw[field.name] = convert_field_to_json(field_data, field_type)
    return type_class(**kw)


def get_field_names(type_class: Type[DataclassProtocol], related_field: FieldName | None = None) -> list[str]:
    """
    Constructs list of fields for Django ORM based on nested dataclasses
    """
    result: list[str] = []
    for field in fields(type_class):
        field_name = field.name if related_field is None else f"{related_field}__{field.name}"
        field_type = remove_optional_from_type(field.type)
        if is_model_schema(field_type):
            sub_names = get_field_names(field_type)
            for sub_name in sub_names:
                result.append(f"{field_name}__{sub_name}")
            if 'id' not in sub_names:
                result.append(f"{field_name}__id")
        else:
            result.append(field_name)
    return result


def reverse_map(
    data: dict[str, Any], reverse_mapping: dict[str, str]
) -> dict[str, Any]:
    return {reverse_mapping.get(k, k): v for k, v in data.items()}




async def get_typed_data(
    type_class: Type[DataclassProtocol],
    qset: models.QuerySet[Any],
    key_fields: tuple[str, ...] = (),
    related_field: FieldName | None = None,
    field_mapping: dict[str, str] = {},
):
    field_names = get_field_names(type_class, related_field=related_field)
    for key_field in key_fields:
        if key_field not in field_names:
            field_names.append(key_field if related_field is None else f"{related_field}__{key_field}")
    result_names = [field_mapping.get(name, name) for name in field_names]
    return qset.values(*result_names)


async def typed_data_dict(
    qset: models.QuerySet[Any],
    type_class: Type[ResultType],
    key_field: FieldName,
    related_field: FieldName | None = None,
) -> FlatDict[ResultType]:
    typed_data = await get_typed_data(type_class, qset, (key_field,), related_field)
    result: dict[ResultKey, ResultType] = {}
    async for row in typed_data:
        obj = get_obj_from_values(type_class, row, related_field=related_field)
        key = row[key_field if related_field is None else f"{related_field}__{key_field}"]
        result[key] = obj
    return result


async def nested_typed_data_dict(
    qset: models.QuerySet[Any],
    type_class: Type[ResultType],
    key_fields: tuple[FieldName, FieldName],
) -> NestedDict[ResultType]:
    """
    In case of composite key, key_field is tuple of field names
    In this case result is two level nested dictionary
    """
    typed_data = await get_typed_data(type_class, qset, key_fields)
    result = defaultdict[ResultKey, dict[ResultKey, ResultType]](dict)
    async for row in typed_data:
        obj = get_obj_from_values(type_class, row)
        key = row[key_fields[0]]
        sub_key = row[key_fields[1]]
        result[key][sub_key] = obj
    return result


def or_pipe(first: Q, second: Q) -> Q:
    return first | second


async def retrieve_typed_dict(
    qset: models.QuerySet[Any],
    result_class: Type[ResultType],
    key_fields: tuple[FieldName, FieldName],
    objs: list[Any],
) -> NestedDict[ResultType]:
    """
    This is used to filter qset by composite key. Composity key components passed in key_field parameter
    objs list is used to filter qset by key_field.
    Main purpose of this function to retrieve object ids during bulk create operation
    """
    if len(objs) == 0:
        return {}
    filter_kwargs = [
        {
            key_fields[0]: getattr(obj, key_fields[0]),
            key_fields[1]: getattr(obj, key_fields[1]),
        }
        for obj in objs
    ]
    filter = reduce(or_pipe, [Q(**kw) for kw in filter_kwargs])
    qset = qset.filter(filter)

    return await nested_typed_data_dict(
        qset=qset, type_class=result_class, key_fields=key_fields
    )


async def typed_data_list(
    qset: models.QuerySet[Any],
    type_class: Type[ResultType],
    field_mapping: dict[str, str] = {},
) -> list[ResultType]:
    result = await get_typed_data(type_class, qset, field_mapping=field_mapping)
    reverse_mapping = {v: k for k, v in field_mapping.items()}
    mapped_result = [reverse_map(row, reverse_mapping) async for row in result]
    return [get_obj_from_values(type_class, row) for row in mapped_result]

