"""Privileged Code mechanism for the sole joint catalog host.

The original joint host authenticates parent/bootstrap BEFORE calling prepare.
This is not a public command entrance or an independent host admission root.
Prepared admissions are hidden and unusable until the original joint host
publishes both legs. No caller-supplied publication setter exists here.
"""

from __future__ import annotations

import inspect
import os
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from threading import RLock
from typing import Any
from weakref import WeakKeyDictionary

from .catalog_epoch_interfaces import (
    CatalogPairEpochExpectation,
    CatalogPublicationExpectation,
    DirectInvocationExpectation,
)
from .catalog_host_interfaces import CatalogJointHost
from .contracts import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticImplementationCoordinate,
    canonical_json_bytes,
)
from .materialization_catalog import (
    AdmittedCodeSemanticContractCatalog,
    CodeSemanticContractCatalog,
    CodeSemanticContractCatalogResolver,
    CodeSemanticDependencyPlanner,
    _issue_code_semantic_contract_catalog,
    _revoke_code_semantic_contract_catalog,
)


class PreparedCodeCatalogLeg:
    """Opaque transaction-local preparation; no public admission fields."""

    def __new__(cls):
        raise TypeError("Code catalog leg is module-issued")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Code catalog leg is sealed")

    def __reduce__(self):
        raise TypeError("Code catalog leg is process-local")


@dataclass(frozen=True)
class _Entrance:
    owner: object
    name: str
    descriptor: object
    method: Callable[..., Any]

    def check(self):
        if inspect.getattr_static(self.owner, self.name) is not self.descriptor:
            raise ContractViolation("original catalog host method substituted")

    def call(self, *args, **kwargs):
        self.check()
        result = self.method(*args, **kwargs)
        self.check()
        return result


def _entrance(owner, name):
    descriptor = inspect.getattr_static(owner, name)
    method = getattr(owner, name)
    if not inspect.ismethod(method) or method.__self__ is not owner:
        raise ContractViolation("original bound host method required")
    return _Entrance(owner, name, descriptor, method)


@dataclass(frozen=True)
class _EpochKey:
    identities: tuple
    values: tuple

    def matches(self, other):
        return (
            len(self.identities) == len(other.identities)
            and all(
                a is b for a, b in zip(self.identities, other.identities, strict=True)
            )
            and self.values == other.values
        )


def _epoch_key(value):
    if (
        type(value) is not CatalogPairEpochExpectation
        or type(value.invocation) is not DirectInvocationExpectation
    ):
        raise TypeError("exact epoch expectation required")
    invocation = value.invocation
    if type(invocation.process_id) is not int or invocation.process_id <= 0:
        raise ContractViolation("exact epoch process required")
    identities = (
        invocation.invocation_identity,
        invocation.lifetime_epoch_identity,
        value.publication_identity,
    )
    if any(v is None for v in identities):
        raise ContractViolation("original epoch identities required")
    digests = (
        value.code_catalog_digest,
        value.membership_catalog_digest,
        value.contribution_digest,
    )
    if any(type(v) is not ContentDigest for v in digests):
        raise TypeError("exact epoch digests required")
    return _EpochKey(
        identities,
        (invocation.process_id, *(ContentDigest(v.value).value for v in digests)),
    )


def _publication_key(value):
    if (
        type(value) is not CatalogPublicationExpectation
        or value.preparation_identity is None
    ):
        raise TypeError("exact publication expectation required")
    successor = _epoch_key(value.successor)
    predecessor = None if value.predecessor is None else _epoch_key(value.predecessor)
    if predecessor is not None and (
        any(
            a is not b
            for a, b in zip(predecessor.identities[:2], successor.identities[:2])
        )
        or predecessor.values[0] != successor.values[0]
        or predecessor.identities[2] is successor.identities[2]
    ):
        raise ContractViolation("publication parent or epoch correspondence differs")
    if type(value.entry_inputs_digest) is not ContentDigest:
        raise TypeError("exact entry-input digest required")
    return _EpochKey(
        (
            value.preparation_identity,
            *successor.identities,
            *((predecessor.identities) if predecessor else ()),
        ),
        (
            predecessor is None,
            *successor.values,
            *((predecessor.values) if predecessor else ()),
            ContentDigest(value.entry_inputs_digest.value).value,
        ),
    )


def _freeze_epoch(value):
    _epoch_key(value)
    i = value.invocation
    return CatalogPairEpochExpectation(
        DirectInvocationExpectation(
            i.invocation_identity, i.lifetime_epoch_identity, i.process_id
        ),
        value.publication_identity,
        deepcopy(value.code_catalog_digest),
        deepcopy(value.membership_catalog_digest),
        deepcopy(value.contribution_digest),
    )


def _freeze_publication(value):
    _publication_key(value)
    return CatalogPublicationExpectation(
        value.preparation_identity,
        None if value.predecessor is None else _freeze_epoch(value.predecessor),
        _freeze_epoch(value.successor),
        deepcopy(value.entry_inputs_digest),
    )


@dataclass
class _EpochPublication:
    expected: CatalogPublicationExpectation
    key: _EpochKey
    prepared: _Entrance
    current: _Entrance
    guard: _Entrance
    preparation: object | None = None

    def check(self):
        if not self.key.matches(_publication_key(self.expected)):
            raise ContractViolation("epoch binding substituted")
        self.prepared.check()
        self.current.check()
        self.guard.check()

    def call(self):
        self.check()
        if self.preparation is None:
            return False
        try:
            argument = _freeze_epoch(self.expected.successor)
            result = self.current.call(self.preparation, expected=argument)
            if not _epoch_key(argument).matches(_epoch_key(self.expected.successor)):
                raise ContractViolation("epoch validation argument changed")
        except Exception:  # noqa: BLE001 -- every original currentness refusal is unavailable
            # Pending and retired epochs are both unusable, not a publication setter.
            self.check()
            return False
        self.check()
        return result is None


@dataclass
class _State:
    pid: int
    source: CodeSemanticContractCatalog
    snapshot: CodeSemanticContractCatalog
    source_bytes: bytes
    parent: _Entrance
    published: _Entrance | _EpochPublication
    preparing: bool = True
    revoked: bool = False
    admission: AdmittedCodeSemanticContractCatalog | None = None

    def validate(self):
        if self.pid != os.getpid() or self.revoked:
            raise ContractViolation("catalog leg no longer live")
        if self.parent.call() is not None:
            raise ContractViolation("parent validator must return None")
        self.published.check()

    def live(self):
        try:
            self.validate()
            # Canonical issuer requires liveness during construction. No handle
            # escapes until preparing is false and publication is owner-controlled.
            return self.preparing or self.published.call() is True
        except Exception:  # noqa: BLE001 -- any owner failure makes admission unavailable
            self.revoked = True
            return False


_STATES: WeakKeyDictionary[PreparedCodeCatalogLeg, _State] = WeakKeyDictionary()
_LOCK = RLock()


def _state(leg):
    if type(leg) is not PreparedCodeCatalogLeg:
        raise TypeError("exact prepared Code leg required")
    state = _STATES.get(leg)
    if state is None:
        raise ContractViolation("foreign or retired Code leg")
    # Before locking: inherited locks may be held by vanished threads.
    if state.pid != os.getpid():
        raise ContractViolation("catalog leg no longer live")
    try:
        state.validate()
    except BaseException:
        revoke_code_catalog_leg(leg)
        raise
    return state


def prepare_code_catalog_leg(
    *,
    joint_host: CatalogJointHost,
    catalog: CodeSemanticContractCatalog,
    provider_executable_bindings: tuple[
        tuple[
            SemanticImplementationCoordinate, SemanticConfigurationCoordinate, object
        ],
        ...,
    ],
    dependency_planner_bindings: tuple[
        tuple[
            SemanticImplementationCoordinate,
            SemanticConfigurationCoordinate,
            CodeSemanticDependencyPlanner,
        ],
        ...,
    ],
    publication: CatalogPublicationExpectation | None = None,
) -> PreparedCodeCatalogLeg:
    """Internal joint operation only; supplied host must ALREADY be authenticated.

    One-time whole-transaction admission and original executable provenance belong
    to that host. This leg validates Code bytes/closure and captures methods once;
    it does not authenticate an arbitrary object merely because callbacks succeed.
    """
    if type(catalog) is not CodeSemanticContractCatalog:
        raise TypeError("exact Code catalog required")
    parent = _entrance(joint_host, "validate_catalog_parent")
    if publication is None:
        published = _entrance(joint_host, "catalogs_published")
    else:
        key = _publication_key(publication)
        if publication.successor.code_catalog_digest != catalog.catalog_root_digest:
            raise ContractViolation("epoch Code catalog digest differs")
        published = _EpochPublication(
            _freeze_publication(publication),
            key,
            _entrance(joint_host, "validate_prepared_catalog_publication"),
            _entrance(joint_host, "validate_current_catalog_epoch"),
            _entrance(joint_host, "validate_catalog_epoch_publication_guard"),
        )
    if parent.call() is not None or published.call() is not False:
        raise ContractViolation("joint host must be live and unpublished")
    initial = canonical_json_bytes(catalog.to_wire())
    snapshot = deepcopy(catalog)
    if (
        canonical_json_bytes(snapshot.to_wire()) != initial
        or canonical_json_bytes(catalog.to_wire()) != initial
    ):
        raise ContractViolation("catalog source moved during capture")
    state = _State(os.getpid(), catalog, snapshot, initial, parent, published)
    try:
        state.admission = _issue_code_semantic_contract_catalog(
            catalog=snapshot,
            provider_executable_bindings=provider_executable_bindings,
            dependency_planner_bindings=dependency_planner_bindings,
            host_liveness=state.live,
        )
        state.validate()
        if (
            canonical_json_bytes(catalog.to_wire()) != initial
            or published.call() is not False
        ):
            raise ContractViolation(
                "catalog source or transaction moved during preparation"
            )
        state.preparing = False
        leg = object.__new__(PreparedCodeCatalogLeg)
        state.validate()
        with _LOCK:
            _STATES[leg] = state
        return leg
    except BaseException:
        state.revoked = True
        state.preparing = False
        if state.admission is not None:
            _revoke_code_semantic_contract_catalog(state.admission)
        raise


def bind_code_catalog_leg_publication(
    leg: PreparedCodeCatalogLeg, preparation: object, guard: object
) -> None:
    """Original joint operation only, after both legs form its nominal preparation.

    This once-only binding closes the prepare/pair ordering without exposing the
    canonical admission. Epoch currentness uses this same original preparation
    handle as its epoch selector; the joint host must check the current record's
    preparation identity. Successful publication never rebinds the leg.
    """
    state = _state(leg)
    binding = state.published
    if type(binding) is not _EpochPublication or preparation is None:
        raise ContractViolation("epoch leg and original preparation required")
    if binding.preparation is not None:
        raise ContractViolation("epoch leg binding replay")
    argument = _freeze_publication(binding.expected)
    result = binding.guard.call(guard, preparation=preparation, expected=argument)
    if not binding.key.matches(_publication_key(argument)):
        raise ContractViolation("preparation validation argument changed")
    if result is not None:
        raise ContractViolation("original publication guard returned non-None")
    state.validate()
    with _LOCK:
        if state.revoked or binding.preparation is not None:
            raise ContractViolation("epoch leg closed or already bound")
        binding.preparation = preparation


def validate_code_catalog_leg(leg: PreparedCodeCatalogLeg) -> None:
    """Original source reread before paired publication; no admission exposure."""
    state = _state(leg)
    try:
        if canonical_json_bytes(state.source.to_wire()) != state.source_bytes:
            raise ContractViolation("Code catalog source moved")
        state.validate()
    except BaseException:
        revoke_code_catalog_leg(leg)
        raise


def code_catalog_leg_snapshot(
    leg: PreparedCodeCatalogLeg,
) -> CodeSemanticContractCatalog:
    """Detached contribution data only; may be used before publication."""
    validate_code_catalog_leg(leg)
    return deepcopy(_state(leg).snapshot)


def published_code_catalog_leg(
    leg: PreparedCodeCatalogLeg,
) -> tuple[AdmittedCodeSemanticContractCatalog, CodeSemanticContractCatalogResolver]:
    """Joint result access only after original paired publication."""
    validate_code_catalog_leg(leg)
    state = _state(leg)
    if state.published.call() is not True or state.admission is None:
        raise ContractViolation("paired catalogs not published")
    resolver = CodeSemanticContractCatalogResolver(state.admission)
    state.validate()
    if state.published.call() is not True:
        raise ContractViolation("paired publication revoked")
    return state.admission, resolver


def revoke_code_catalog_leg(leg: PreparedCodeCatalogLeg) -> None:
    """Idempotent owner rollback, including when original parent already closed."""
    if type(leg) is not PreparedCodeCatalogLeg:
        raise TypeError("exact prepared Code leg required")
    state = _STATES.get(leg)
    if state is None:
        return
    if state.pid != os.getpid():
        raise ContractViolation("catalog leg process changed")
    with _LOCK:
        state.revoked = True
        if state.admission is not None:
            _revoke_code_semantic_contract_catalog(state.admission)
        _STATES.pop(leg, None)
