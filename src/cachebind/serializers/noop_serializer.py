"""No-op serializer."""

from typing import cast

from cachebind.serializers.serializer import Serializer


class NoopSerializer[ValueType, StorageType](Serializer[ValueType, StorageType]):
    """Identity when value and storage types match.

    When they differ, this instance is only a build-time placeholder. Pass
    ``serializer=`` on index calls that serialize or deserialize.
    """

    def serialize(self, value: ValueType) -> StorageType:
        return cast(StorageType, value)

    def deserialize(self, value: StorageType) -> ValueType:
        return cast(ValueType, value)