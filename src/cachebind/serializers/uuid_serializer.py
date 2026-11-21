"""UUID serializer."""

from uuid import UUID

from cachebind.serializers.serializer import Serializer


class UuidSerializer(Serializer[UUID, str]):
    """Canonical UUID text via ``str(uuid)``."""

    def serialize(self, value: UUID) -> str:
        if not isinstance(value, UUID):
            raise ValueError(f"expected UUID, got {type(value).__name__}")
        return str(value)

    def deserialize(self, value: str) -> UUID:
        if not isinstance(value, str):
            raise ValueError(f"invalid UUID: {value!r}")
        try:
            return UUID(value)
        except ValueError as exc:
            raise ValueError(f"invalid UUID: {value!r}") from exc