"""Choose the serializer for one index call."""

from collections.abc import Mapping
from typing import Any, cast

from cachebind.serializers.serializer import Serializer


def resolve_serializer[ValueType, StorageType](
    index_serializer: Serializer[ValueType, StorageType],
    kwargs: Mapping[str, Any],
) -> Serializer[ValueType, StorageType]:
    """Return ``kwargs['serializer']`` when set, otherwise the index serializer."""
    override = kwargs.get("serializer")
    if override is None:
        return index_serializer
    return cast(Serializer[ValueType, StorageType], override)