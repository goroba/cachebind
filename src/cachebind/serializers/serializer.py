"""Serializer."""

from abc import ABC, abstractmethod
from collections.abc import Sequence


class Serializer[ValueType, StorageType](ABC):
    """Convert a Python value to a storage value and back."""

    @abstractmethod
    def serialize(self, value: ValueType) -> StorageType:
        """Convert ``value`` into its storage representation."""
        ...

    @abstractmethod
    def deserialize(self, value: StorageType) -> ValueType:
        """Restore a Python value from its storage representation."""
        ...

    def mserialize(self, values: Sequence[ValueType]) -> list[StorageType]:
        """Convert each value into its storage representation, in input order."""
        return [self.serialize(value) for value in values]

    def mdeserialize(self, values: Sequence[StorageType]) -> list[ValueType]:
        """Restore each value from its storage representation, in input order."""
        return [self.deserialize(value) for value in values]
