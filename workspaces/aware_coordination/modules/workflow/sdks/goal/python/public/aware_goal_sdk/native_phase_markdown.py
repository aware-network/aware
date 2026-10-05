"""Byte-exact Markdown carrier for native Goal Lane/Phase authority."""

from __future__ import annotations

import hashlib

from aware_goal_operational_runtime import (
    GoalPhaseContractBundleV1,
    GoalPhaseNativeDocumentV1,
    GoalPhaseNativeDocumentV2,
    GoalPhaseNativeDocumentV3,
    GoalPhaseNativeCarrierError,
    GOAL_PHASE_NATIVE_START_MARKER,
    GOAL_PHASE_NATIVE_END_MARKER,
    attach_goal_phase_native_carrier,
    extract_goal_phase_native_carrier,
    encode_goal_phase_native_document,
)

from .dependency_source import parse_goal_dependency_source
from .phase_markdown_projection import project_goal_phase_markdown

START_MARKER = GOAL_PHASE_NATIVE_START_MARKER
END_MARKER = GOAL_PHASE_NATIVE_END_MARKER
_OPEN = START_MARKER + b"\n```json\n"
_CLOSE = b"\n```\n" + END_MARKER + b"\n"


class GoalPhaseNativeMarkdownError(ValueError):
    """Native authority block is missing, duplicated, or not byte-bound."""


def attach_goal_phase_native_document(
    compatibility_markdown: bytes,
    document: GoalPhaseNativeDocumentV1 | GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3,
) -> bytes:
    """Append one canonical terminal authority block without rewriting Markdown."""

    _ = _bytes(compatibility_markdown, "compatibility_markdown")
    if START_MARKER in compatibility_markdown or END_MARKER in compatibility_markdown:
        raise GoalPhaseNativeMarkdownError("compatibility Markdown already has markers")
    _verify_compatibility_binding(compatibility_markdown, document)
    try:
        return attach_goal_phase_native_carrier(compatibility_markdown, document)
    except GoalPhaseNativeCarrierError as error:
        raise GoalPhaseNativeMarkdownError(str(error)) from error


def extract_goal_phase_native_document(
    candidate: bytes,
) -> tuple[bytes, GoalPhaseNativeDocumentV1 | GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3]:
    """Recover the exact legacy prefix and strict native authority document."""

    try:
        compatibility, document = extract_goal_phase_native_carrier(candidate)
    except GoalPhaseNativeCarrierError as error:
        raise GoalPhaseNativeMarkdownError(str(error)) from error
    _verify_compatibility_binding(compatibility, document)
    return compatibility, document


def repair_advanced_goal_phase_native_document(
    *,
    prior_candidate: bytes,
    advanced_candidate: bytes,
    source_refs: tuple[str, ...],
) -> tuple[bytes, GoalPhaseNativeDocumentV1 | GoalPhaseNativeDocumentV2]:
    """Rebind one unchanged native graph after compatibility-only advancement.

    This is deliberately narrower than a migration or native semantic mutation.
    The prior carrier must be canonical. The advanced bytes must contain that
    exact authority block once, possibly with compatibility changes before and
    after it. Phase coordinates, order, legacy Gate meaning, and authored
    dependencies must remain unchanged.
    """

    prior_compatibility, prior_document = extract_goal_phase_native_document(
        prior_candidate
    )
    if type(prior_document) is GoalPhaseNativeDocumentV3:
        raise GoalPhaseNativeMarkdownError(
            "V3 compatibility repair requires a separate preservation law"
        )
    start = advanced_candidate.find(_OPEN)
    if start < 0 or advanced_candidate.find(_OPEN, start + len(_OPEN)) >= 0:
        raise GoalPhaseNativeMarkdownError(
            "advanced candidate must contain one authority block"
        )
    close = advanced_candidate.find(_CLOSE, start + len(_OPEN))
    if close < 0 or advanced_candidate.find(_CLOSE, close + len(_CLOSE)) >= 0:
        raise GoalPhaseNativeMarkdownError(
            "advanced candidate must contain one authority block close"
        )
    payload = advanced_candidate[start + len(_OPEN) : close]
    if payload != encode_goal_phase_native_document(prior_document):
        raise GoalPhaseNativeMarkdownError(
            "advanced authority block differs from prior native document"
        )
    compatibility = advanced_candidate[:start] + advanced_candidate[
        close + len(_CLOSE) :
    ]
    if START_MARKER in compatibility or END_MARKER in compatibility:
        raise GoalPhaseNativeMarkdownError(
            "advanced compatibility contains native authority markers"
        )
    try:
        prior_projection = project_goal_phase_markdown(
            prior_compatibility.decode("utf-8")
        )
        advanced_projection = project_goal_phase_markdown(
            compatibility.decode("utf-8")
        )
        prior_dependencies = parse_goal_dependency_source(
            prior_compatibility.decode("utf-8")
        ).dependencies
        advanced_dependencies = parse_goal_dependency_source(
            compatibility.decode("utf-8")
        ).dependencies
    except (UnicodeDecodeError, ValueError) as error:
        raise GoalPhaseNativeMarkdownError(
            "advanced compatibility is not a valid legacy Goal projection"
        ) from error
    prior_phase_meaning = tuple(
        (phase.coordinate, phase.ordinal, phase.gate)
        for phase in prior_projection.phases
    )
    advanced_phase_meaning = tuple(
        (phase.coordinate, phase.ordinal, phase.gate)
        for phase in advanced_projection.phases
    )
    if (
        advanced_projection.goal_tag != prior_projection.goal_tag
        or advanced_phase_meaning != prior_phase_meaning
        or advanced_dependencies != prior_dependencies
    ):
        raise GoalPhaseNativeMarkdownError(
            "advanced compatibility changes native Phase or dependency meaning"
        )
    compatibility_digest = "sha256:" + hashlib.sha256(compatibility).hexdigest()
    if type(prior_document) is GoalPhaseNativeDocumentV2:
        rebound: GoalPhaseNativeDocumentV1 | GoalPhaseNativeDocumentV2 = GoalPhaseNativeDocumentV2(
            goal_tag=prior_document.goal_tag,
            compatibility_projection_sha256=compatibility_digest,
            compatibility_projection_byte_count=len(compatibility),
            definitions=prior_document.definitions,
            operational_bundle=prior_document.operational_bundle,
            unresolved_dependencies=prior_document.unresolved_dependencies,
            source_refs=source_refs,
            execution_authority=prior_document.execution_authority,
        )
    else:
        rebound = GoalPhaseNativeDocumentV1(
            goal_tag=prior_document.goal_tag,
            compatibility_projection_sha256=compatibility_digest,
            compatibility_projection_byte_count=len(compatibility),
            definitions=prior_document.definitions,
            operational_bundle=prior_document.operational_bundle,
            unresolved_dependencies=prior_document.unresolved_dependencies,
            source_refs=source_refs,
        )
    return attach_goal_phase_native_document(compatibility, rebound), rebound


def withdraw_goal_phase_native_dependency(
    *,
    candidate: bytes,
    corrected_compatibility: bytes,
    dependency_key: str,
) -> tuple[bytes, GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV2]:
    """Remove one exact V2 edge in lockstep with its Markdown declaration.

    The caller supplies the corrected compatibility projection; this function
    proves it differs by precisely the named declaration before rebinding the
    native carrier. It never infers a replacement edge or a Gate result.
    """

    before_compatibility, before = extract_goal_phase_native_document(candidate)
    if type(before) is not GoalPhaseNativeDocumentV2:
        raise GoalPhaseNativeMarkdownError("withdrawal requires an operational V2 Goal")
    if type(dependency_key) is not str or not dependency_key:
        raise GoalPhaseNativeMarkdownError("dependency_key must be nonempty text")
    try:
        before_declarations = parse_goal_dependency_source(
            before_compatibility.decode("utf-8")
        ).dependencies
        after_declarations = parse_goal_dependency_source(
            corrected_compatibility.decode("utf-8")
        ).dependencies
    except (UnicodeDecodeError, ValueError, KeyError, TypeError) as error:
        raise GoalPhaseNativeMarkdownError("invalid dependency projection") from error
    matching = tuple(
        item for item in before_declarations if item.dependency_key == dependency_key
    )
    if len(matching) != 1 or after_declarations != tuple(
        item for item in before_declarations if item.dependency_key != dependency_key
    ):
        raise GoalPhaseNativeMarkdownError(
            "compatibility must withdraw exactly one named declaration"
        )
    native_dependencies = before.operational_bundle.dependencies
    native_all = (*native_dependencies, *before.unresolved_dependencies)
    if not {item.dependency_key for item in before_declarations}.issubset(
        {item.dependency_key for item in native_all}
    ):
        raise GoalPhaseNativeMarkdownError(
            "Markdown declaration lacks matching native dependency"
        )
    for authored in before_declarations:
        native_authored = next(
            item for item in native_all if item.dependency_key == authored.dependency_key
        )
        if (
            native_authored.owner_goal_tag != authored.owner_goal_tag
            or native_authored.dependent.goal_tag != authored.owner_goal_tag
            or native_authored.dependent.lane_key != authored.dependent_lane_key
            or native_authored.dependent.phase_key != authored.dependent_row_key
            or native_authored.prerequisite.goal_tag != authored.prerequisite_goal_tag
            or native_authored.prerequisite.lane_key != authored.prerequisite_lane_key
            or native_authored.prerequisite.phase_key != authored.prerequisite_row_key
            or native_authored.relation != authored.relation
            or native_authored.reason != authored.reason
            or native_authored.evidence_refs != tuple(sorted(authored.evidence_refs))
        ):
            raise GoalPhaseNativeMarkdownError(
                "Markdown and native dependency definitions differ"
            )
    native_matches = tuple(
        item for item in native_dependencies if item.dependency_key == dependency_key
    )
    if len(native_matches) != 1:
        raise GoalPhaseNativeMarkdownError(
            "named dependency must occur exactly once in native authority"
        )
    after_bundle = GoalPhaseContractBundleV1(
        phases=before.operational_bundle.phases,
        dependencies=tuple(
            item for item in native_dependencies if item.dependency_key != dependency_key
        ),
    )
    after = GoalPhaseNativeDocumentV2(
        goal_tag=before.goal_tag,
        compatibility_projection_sha256=(
            "sha256:" + hashlib.sha256(corrected_compatibility).hexdigest()
        ),
        compatibility_projection_byte_count=len(corrected_compatibility),
        definitions=before.definitions,
        operational_bundle=after_bundle,
        unresolved_dependencies=before.unresolved_dependencies,
        source_refs=before.source_refs,
        execution_authority=before.execution_authority,
    )
    return attach_goal_phase_native_document(corrected_compatibility, after), before, after


def _verify_compatibility_binding(
    compatibility: bytes,
    document: GoalPhaseNativeDocumentV1 | GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3,
) -> None:
    if type(document) not in {
        GoalPhaseNativeDocumentV1, GoalPhaseNativeDocumentV2,
        GoalPhaseNativeDocumentV3,
    }:
        raise TypeError("document must be an exact native Goal document")
    document.__post_init__()
    try:
        projection = project_goal_phase_markdown(compatibility.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as error:
        raise GoalPhaseNativeMarkdownError(
            "compatibility prefix is not a valid legacy Goal projection"
        ) from error
    if projection.goal_tag != document.goal_tag:
        raise GoalPhaseNativeMarkdownError(
            "native document Goal differs from compatibility Goal"
        )
    digest = "sha256:" + hashlib.sha256(compatibility).hexdigest()
    if (
        len(compatibility) != document.compatibility_projection_byte_count
        or digest != document.compatibility_projection_sha256
    ):
        raise GoalPhaseNativeMarkdownError(
            "native document does not bind the exact compatibility Markdown"
        )


def _bytes(value: object, name: str) -> bytes:
    if type(value) is not bytes:
        raise TypeError(f"{name} must be exact bytes")
    return value


__all__ = [
    "END_MARKER",
    "START_MARKER",
    "GoalPhaseNativeMarkdownError",
    "attach_goal_phase_native_document",
    "extract_goal_phase_native_document",
    "repair_advanced_goal_phase_native_document",
    "withdraw_goal_phase_native_dependency",
]
