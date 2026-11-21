"""Breadcrumb helpers for index writes."""


def storage_identifier(value: object) -> str:
    """Turn a serialized storage value into the identifier string used in breadcrumbs."""
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)