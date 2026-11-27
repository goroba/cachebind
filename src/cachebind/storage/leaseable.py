"""Fill-lease operations for key-value storage."""



from abc import ABC, abstractmethod
class LeasableKeyValueStorage[ClientType](ABC):
    """Synchronous key-value storage that can acquire and release a per-field fill lease."""

    @abstractmethod
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

    @abstractmethod
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


class AsyncLeasableKeyValueStorage[ClientType](ABC):
    """Asynchronous key-value storage that can acquire and release a per-field fill lease."""

    @abstractmethod
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

    @abstractmethod
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