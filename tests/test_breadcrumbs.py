import pytest

from cachebind.tagging import ColonBreadcrumbs, NoopBreadcrumbs


def test_colon_round_trip() -> None:
    crumbs = ColonBreadcrumbs()
    assert crumbs.encode("users", "42") == "users:42"
    assert crumbs.decode("users:42") == ("users", "42")
    assert crumbs.decode(crumbs.encode("users", "42")) == ("users", "42")


def test_colon_identifier_may_contain_colon() -> None:
    crumbs = ColonBreadcrumbs()
    assert crumbs.encode("users", "a:b") == "users:a:b"
    assert crumbs.decode("users:a:b") == ("users", "a:b")
    assert crumbs.decode(crumbs.encode("users", "a:b")) == ("users", "a:b")


def test_colon_rejects_missing_separator() -> None:
    with pytest.raises(ValueError):
        ColonBreadcrumbs().decode("users")


def test_noop_encode_is_empty() -> None:
    crumbs = NoopBreadcrumbs()
    assert crumbs.encode("users", "42") == ""
    assert crumbs.decode("") == ("", "")
    assert crumbs.decode(crumbs.encode("users", "42")) == ("", "")


def test_noop_rejects_non_empty_breadcrumb() -> None:
    with pytest.raises(ValueError):
        NoopBreadcrumbs().decode("users:42")