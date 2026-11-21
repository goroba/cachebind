"""No-op breadcrumbs."""

from cachebind.tagging.breadcrumbs.protocol import Breadcrumbs


class NoopBreadcrumbs(Breadcrumbs):
    """Always encode to an empty breadcrumb string."""

    def encode(self, index: str, identifier: str) -> str:
        return ""

    def decode(self, value: str) -> tuple[str, str]:
        if value != "":
            raise ValueError(f"invalid breadcrumb: {value!r}")
        return "", ""