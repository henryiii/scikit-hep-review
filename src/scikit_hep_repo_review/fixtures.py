from __future__ import annotations

import graphlib
import importlib.metadata
import inspect
import typing
from collections.abc import Callable, Mapping
from typing import Any

from ._compat import tomllib
from ._compat.importlib.resources.abc import Traversable

__all__ = [
    "pyproject",
    "package",
    "compute_fixtures",
    "apply_fixtures",
    "collect_fixtures",
]


def __dir__() -> list[str]:
    return __all__


def pyproject(package: Traversable) -> dict[str, Any]:
    pyproject_path = package.joinpath("pyproject.toml")
    if pyproject_path.is_file():
        with pyproject_path.open("rb") as f:
            return tomllib.load(f)
    return {}


def package(package: Traversable) -> Traversable:
    return package


def compute_fixtures(
    package: Traversable, fixtures: Mapping[str, Callable[..., Any]]
) -> dict[str, Any]:
    results: dict[str, Any] = {"package": package}
    graph = {
        name: set() if name == "package" else inspect.signature(fix).parameters.keys()
        for name, fix in fixtures.items()
    }
    ts = graphlib.TopologicalSorter(graph)
    for fixture_name in ts.static_order():
        if fixture_name == "package":
            continue
        func = fixtures[fixture_name]
        signature = inspect.signature(func)
        kwargs = {name: results[name] for name in signature.parameters}
        results[fixture_name] = fixtures[fixture_name](**kwargs)
    return results


T = typing.TypeVar("T")


def apply_fixtures(computed_fixtures: Mapping[str, Any], func: Callable[..., T]) -> T:
    signature = inspect.signature(func)
    kwargs = {
        name: value
        for name, value in computed_fixtures.items()
        if name in signature.parameters
    }
    return func(**kwargs)


def collect_fixtures() -> dict[str, Callable[[Traversable], Any]]:
    return {
        ep.name: ep.load()
        for ep in importlib.metadata.entry_points(
            group="scikit_hep_repo_review.fixtures"
        )
    }
