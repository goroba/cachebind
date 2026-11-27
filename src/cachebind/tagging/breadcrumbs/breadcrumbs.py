"""Breadcrumbs."""

from abc import ABC, abstractmethod


class Breadcrumbs(ABC):
    """Encode an index and an identifier into one string, and split that string back."""

    @abstractmethod
    def encode(self, index: str, identifier: str) -> str:
        """Join ``index`` and ``identifier`` into one string."""
        ...

    @abstractmethod
    def decode(self, value: str) -> tuple[str, str]:
        """Split ``value`` into the index and the identifier."""
        ...
