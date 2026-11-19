"""No-op serializer."""

from cachebind.serializers.serializer import Serializer


class NoopSerializer[ValueType](Serializer[ValueType, ValueType]):
    """Identity serializer when the storage value is already the model value."""

    def serialize(self, value: ValueType) -> ValueType:
        return value

    def deserialize(self, value: ValueType) -> ValueType:
        return value