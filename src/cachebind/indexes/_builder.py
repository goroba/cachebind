"""Shared checks for building a registered index."""

import types
from abc import ABC
from typing import Any, Generic, TypeVar, get_args, get_origin

from cachebind.indexes.base import get_registry
from cachebind.serializers.serializer import Serializer


def check_key(key: str) -> None:
    if not isinstance(key, str) or key == "":
        raise TypeError(f"index key must be a non-empty str, got {key!r}")


def instance_class(key: str, value: Any, *, label: str) -> type:
    if isinstance(value, type):
        raise TypeError(f"index {key!r}: {label} must be an instance, got class {value.__name__}")
    return type(value)


def serializer_class(serializer: Any) -> type:
    if isinstance(serializer, type):
        return serializer
    orig = getattr(serializer, "__orig_class__", None)
    if orig is not None:
        return orig
    return type(serializer)


def serializer_types(key: str, serializer: Any) -> tuple[Any, Any]:
    alias_args = get_args(serializer)
    if alias_args and len(alias_args) == 2:
        return alias_args
    if not isinstance(serializer, type):
        raise TypeError(
            f"index {key!r}: serializer must be a class, got {type(serializer).__name__}"
        )
    args = generic_args(serializer, Serializer)
    if args is None or len(args) != 2:
        raise TypeError(
            f"index {key!r}: {serializer.__name__} does not declare "
            "Serializer[ValueType, StorageType]"
        )
    return args


def check_value_type(key: str, declared: Any, value_type: Any, *, label: str) -> None:
    if value_matches(value_type, declared):
        return
    raise TypeError(
        f"index {key!r}: {label} {declared!r} does not match "
        f"serializer value type {value_type!r}"
    )


def storage_client_type(key: str, storage: Any, interface: type) -> type:
    args = generic_args(storage, interface)
    if args and isinstance(args[0], type):
        return args[0]
    name = storage.__name__ if isinstance(storage, type) else type(storage).__name__
    raise TypeError(f"index {key!r}: {name} client type must be a class")


def check_storage_type(key: str, serializer_storage: Any, storage_type: Any, storage: Any) -> None:
    if serializer_storage != storage_type:
        raise TypeError(
            f"index {key!r}: serializer storage type {serializer_storage!r} "
            f"does not match {storage.__name__} storage type {storage_type!r}"
        )


def value_matches(value_type: Any, declared: Any) -> bool:
    if not isinstance(value_type, TypeVar):
        return declared == value_type
    constraints = value_type.__constraints__
    if constraints:
        return any(
            declared == constraint or _is_subclass(declared, constraint)
            for constraint in constraints
        )
    bound = value_type.__bound__
    if bound is None:
        return isinstance(declared, type)
    return _is_subclass(declared, bound)


def generic_args(cls: Any, interface: type) -> tuple[Any, ...] | None:
    return _walk_generic_args(cls, interface, {}, ())


def index_class(
    key: str,
    *,
    serializer_instance: Any,
    storage: Any,
    base: type,
    module: str,
    attributes: dict[str, Any],
) -> Any:
    suffix = "".join(char if char.isalnum() else "_" for char in key)
    namespace: dict[str, Any] = {
        "__module__": module,
        "serializer": serializer_instance,
        "key": key,
        "storage": storage,
    }
    namespace.update(attributes)
    type(f"{base.__name__}_{suffix}", (base,), namespace)
    return get_registry(attributes["client_type"]).get(key)


def _is_subclass(declared: Any, parent: Any) -> bool:
    if not isinstance(declared, type):
        return False
    origin = get_origin(parent)
    parent_type = origin if isinstance(origin, type) else parent
    if not isinstance(parent_type, type):
        return False
    try:
        return issubclass(declared, parent_type)
    except TypeError:
        return False


def _walk_generic_args(
    cls: Any,
    interface: type,
    subst: dict[Any, Any],
    stack: tuple[type, ...],
) -> tuple[Any, ...] | None:
    if not isinstance(cls, type) or cls in stack or cls in {object, ABC, Generic}:
        return None
    stack = (*stack, cls)
    for base in types.get_original_bases(cls):
        origin = get_origin(base)
        if origin is None:
            found = _walk_generic_args(base, interface, subst, stack)
            if found is not None:
                return found
            continue
        if origin is interface:
            return tuple(_substitute(arg, subst) for arg in get_args(base))
        if not isinstance(origin, type):
            continue
        args = get_args(base)
        params = getattr(origin, "__type_params__", ())
        local = dict(subst)
        if len(params) == len(args):
            for param, arg in zip(params, args, strict=True):
                local[param] = _substitute(arg, subst)
        found = _walk_generic_args(origin, interface, local, stack)
        if found is not None:
            return found
    return None


def _substitute(tp: Any, subst: dict[Any, Any]) -> Any:
    if isinstance(tp, TypeVar):
        return subst.get(tp, tp)
    origin = get_origin(tp)
    if origin is None:
        return tp
    args = get_args(tp)
    substituted = tuple(_substitute(arg, subst) for arg in args)
    if substituted == args:
        return tp
    try:
        return origin[substituted]
    except TypeError:
        return tp

