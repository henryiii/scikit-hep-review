from __future__ import annotations

import importlib.metadata
from collections.abc import Mapping, Set
from typing import Any, ClassVar, Protocol

from ..fixtures import apply_fixtures

__all__ = ["Check", "collect_checks", "is_allowed"]


class Check(Protocol):
    family: ClassVar[str]
    requires: ClassVar[Set[str]] = frozenset()

    def check(self) -> bool | None:
        ...


def collect_checks(fixtures: Mapping[str, Any]) -> dict[str, Check]:
    check_functions = (
        ep.load()
        for ep in importlib.metadata.entry_points(group="scikit_hep_repo_review.checks")
    )

    return {
        k: v
        for func in check_functions
        for k, v in apply_fixtures(fixtures, func).items()
    }


def is_allowed(ignore_list: Set[str], name: str) -> bool:
    """
    Skips the check if the name is in the ignore list or if the name without
    the number is in the ignore list.
    """
    if name in ignore_list:
        return False
    if name.rstrip("0123456789") in ignore_list:
        return False
    return True
