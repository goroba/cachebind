"""Fill-lease operations for key-value storage."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class LeasableKeyValueStorage[ClientType](Protocol):
    """Synchronous key-value storage that can acquire and release a per-field fill lease."""

    def try_acquire_lease(
        self,
        client: ClientType,
        name: str,
        field: str,
        *,
        token: str,
        lease_ttl: int,
    ) -> bool:
        """Try to take the fill lease for ``field``.

        Return ``False`` when the field already has a value or another holder owns the lease.
        """
        ...

    def release_lease(
        self,
        client: ClientType,
        name: str,
        field: str,
        *,
        token: str,
    ) -> None:
        """Release the fill lease when ``token`` still matches."""
        ...


@runtime_checkable
class AsyncLeasableKeyValueStorage[ClientType](Protocol):
    """Asynchronous key-value storage that can acquire and release a per-field fill lease."""

    async def try_acquire_lease(
        self,
        client: ClientType,
        name: str,
        field: str,
        *,
        token: str,
        lease_ttl: int,
    ) -> bool:
        """Try to take the fill lease for ``field``.

        Return ``False`` when the field already has a value or another holder owns the lease.
        """
        ...

    async def release_lease(
        self,
        client: ClientType,
        name: str,
        field: str,
        *,
        token: str,
    ) -> None:
        """Release the fill lease when ``token`` still matches."""
        ...