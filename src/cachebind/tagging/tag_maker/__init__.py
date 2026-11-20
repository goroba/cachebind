"""Tag makers encode an index and an identifier into one string."""

from cachebind.tagging.tag_maker.colon_tag_maker import ColonTagMaker
from cachebind.tagging.tag_maker.noop_tag_maker import NoopTagMaker
from cachebind.tagging.tag_maker.protocol import TagMaker

__all__ = [
    "ColonTagMaker",
    "NoopTagMaker",
    "TagMaker",
]