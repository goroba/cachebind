"""Breadcrumbs encode an index and an identifier into one string."""

from cachebind.tagging.breadcrumbs.colon_breadcrumbs import ColonBreadcrumbs
from cachebind.tagging.breadcrumbs.noop_breadcrumbs import NoopBreadcrumbs
from cachebind.tagging.breadcrumbs.breadcrumbs import Breadcrumbs

__all__ = [
    "Breadcrumbs",
    "ColonBreadcrumbs",
    "NoopBreadcrumbs",
]