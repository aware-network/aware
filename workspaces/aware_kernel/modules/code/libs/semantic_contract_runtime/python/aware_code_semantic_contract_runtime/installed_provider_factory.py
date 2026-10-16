"""Canonical installed factory intake; metadata is not execution authority.

Retained profiles supply root keys; qualified applications supply fixed product
metadata. Loading may import code. Neither entrance executes a factory.
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from importlib.metadata import EntryPoint, entry_points
from threading import RLock
from types import FunctionType
from typing import cast

from .contracts import ContractViolation
from .selected_provider import (
    SelectedProviderStageFactoryProduct,
    _admit_selected_provider_factory,
    _AdmittedSemanticProviderFactory,
    _factory_state,
    _SelectedProviderFactoryProduct,
)

_GROUP = "aware.code.semantic_contract.stage_factory.v1"
_LOCK = RLock()
_ADMISSIONS: dict[str, tuple[int, EntryPoint, _AdmittedSemanticProviderFactory]] = {}
_CREATOR_PID = os.getpid()


def _product_text(value: object, limit: int) -> str:
    if type(value) is not str:
        raise TypeError("exact product metadata text required")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError as exc:
        raise ContractViolation("product metadata must be UTF-8") from exc
    if not 1 <= size <= limit or any(c.isspace() for c in value):
        raise ContractViolation("product metadata must be a bounded nonblank token")
    return value


def _target(value: str) -> tuple[str, str]:
    parts = value.split(":")
    if len(parts) != 2 or any(
        not component.isidentifier() for part in parts for component in part.split(".")
    ):
        raise ContractViolation(
            "product target must be exact module:function without extras"
        )
    return parts[0], parts[1]


def _distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _product_metadata(entry: EntryPoint, expected: tuple[str, str]) -> None:
    distribution, target = expected
    if entry.group != _GROUP or entry.value != target:
        raise ContractViolation("installed product target differs")
    if entry.dist is None:
        raise ContractViolation("installed product distribution provenance unavailable")
    name = _product_text(entry.dist.metadata["Name"], 512)
    if _distribution_name(name) != _distribution_name(distribution):
        raise ContractViolation("installed product distribution differs")


def _product_function(factory: object, target: str) -> None:
    module, qualname = _target(target)
    if (
        type(factory) is not FunctionType
        or type(factory.__module__) is not str
        or type(factory.__qualname__) is not str
        or factory.__module__ != module
        or factory.__qualname__ != qualname
    ):
        raise ContractViolation("loaded product function differs from selected target")


def _admit_installed(
    provider_key: str, expected: tuple[str, str] | None
) -> _AdmittedSemanticProviderFactory:
    # One original lookup/lock/cache, preserving key-only root behavior.
    if type(provider_key) is not str or not provider_key:
        raise TypeError("exact selected semantic provider key required")
    candidates = tuple(
        item for item in entry_points(group=_GROUP) if item.name == provider_key
    )
    if len(candidates) != 1:
        raise ContractViolation("unique installed semantic provider factory required")
    entry = candidates[0]
    if type(entry) is not EntryPoint:
        raise TypeError("exact installed entry point required")
    if type(entry.value) is not str or not entry.value:
        raise ContractViolation("installed factory entrance unavailable")
    with _LOCK:
        if expected is not None:
            _product_metadata(entry, expected)
        retained = _ADMISSIONS.get(provider_key)
        if retained is not None:
            pid, original, admission = retained
            if pid != os.getpid() or original != entry:
                raise ContractViolation("installed provider factory selection changed")
            state = _factory_state(admission)
            if state.provider_key != provider_key:
                raise ContractViolation("installed provider key changed")
            if expected is not None:
                _product_function(state.selection_factory, expected[1])
            return admission
        factory = entry.load()
        if expected is not None:
            _product_function(factory, expected[1])
        admission = _admit_selected_provider_factory(
            factory_ref=f"installed:{_GROUP}:{provider_key}:{entry.value}",
            provider_key=provider_key,
            selection_factory=cast(
                Callable[
                    [],
                    _SelectedProviderFactoryProduct
                    | SelectedProviderStageFactoryProduct,
                ],
                factory,
            ),
        )
        _ADMISSIONS[provider_key] = (os.getpid(), entry, admission)
        return admission


def admit_installed_semantic_stage_factory(
    provider_key: str,
) -> _AdmittedSemanticProviderFactory:
    """Original root function over the one canonical lookup/cache.

    The caller derives its key from the retained profile. This is not source,
    catalog, package, epoch, selected execution or installed-byte authority.
    """
    return _admit_installed(provider_key, None)


def admit_installed_semantic_product_factory(
    provider_key: str,
    *,
    expected_distribution: str,
    expected_entrypoint: str,
) -> _AdmittedSemanticProviderFactory:
    """Check qualified fixed metadata, never derived from user/request TOML."""
    if os.getpid() != _CREATOR_PID:
        raise ContractViolation("installed product intake belongs to another process")
    key = _product_text(provider_key, 512)
    distribution = _product_text(expected_distribution, 512)
    target = _product_text(expected_entrypoint, 4096)
    _ = _target(target)
    return _admit_installed(key, (distribution, target))


__all__ = [
    "admit_installed_semantic_stage_factory",
    "admit_installed_semantic_product_factory",
]
