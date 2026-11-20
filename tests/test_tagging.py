import pytest

from cachebind.tagging import ColonTagMaker, NoopTagMaker


def test_colon_round_trip() -> None:
    tag_maker = ColonTagMaker()
    assert tag_maker.encode("users", "42") == "users:42"
    assert tag_maker.decode("users:42") == ("users", "42")
    assert tag_maker.decode(tag_maker.encode("users", "42")) == ("users", "42")


def test_colon_identifier_may_contain_colon() -> None:
    tag_maker = ColonTagMaker()
    assert tag_maker.encode("users", "a:b") == "users:a:b"
    assert tag_maker.decode("users:a:b") == ("users", "a:b")
    assert tag_maker.decode(tag_maker.encode("users", "a:b")) == ("users", "a:b")


def test_colon_rejects_missing_separator() -> None:
    with pytest.raises(ValueError):
        ColonTagMaker().decode("users")


def test_noop_encode_is_empty() -> None:
    tag_maker = NoopTagMaker()
    assert tag_maker.encode("users", "42") == ""
    assert tag_maker.decode("") == ("", "")
    assert tag_maker.decode(tag_maker.encode("users", "42")) == ("", "")


def test_noop_rejects_non_empty_tag() -> None:
    with pytest.raises(ValueError):
        NoopTagMaker().decode("users:42")