"""No-op tag maker."""

from cachebind.tagging.tag_maker.protocol import TagMaker


class NoopTagMaker(TagMaker):
    """Always encode to an empty tag string."""

    def encode(self, index: str, identifier: str) -> str:
        return ""

    def decode(self, value: str) -> tuple[str, str]:
        if value != "":
            raise ValueError(f"invalid tag: {value!r}")
        return "", ""