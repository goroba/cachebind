"""Tags encode an index and an identifier into one string."""

from cachebind.tagging.tag_maker import ColonTagMaker, NoopTagMaker, TagMaker

__all__ = [
    "ColonTagMaker",
    "NoopTagMaker",
    "TagMaker",
]