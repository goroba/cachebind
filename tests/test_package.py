from importlib.metadata import requires

import cachebind


def test_import() -> None:
    assert cachebind.__version__


def test_optional_extras() -> None:
    declared = requires("cachebind") or []
    extras = {
        requirement.split("extra == ")[-1].strip().strip("'\"")
        for requirement in declared
        if "extra ==" in requirement
    }
    assert {"redis", "pydantic"} <= extras
