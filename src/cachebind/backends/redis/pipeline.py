"""Pipeline helpers for batched Redis writes."""


def execute_if_queued(pipe: object, queued: bool) -> None:
    if queued:
        pipe.execute()  # type: ignore[attr-defined]


async def async_execute_if_queued(pipe: object, queued: bool) -> None:
    if queued:
        await pipe.execute()  # type: ignore[attr-defined]