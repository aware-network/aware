from __future__ import annotations

from pathlib import Path
import re
import sys

import pytest
from aware_meta_sdk import (
    FunctionCoverageSkip,
    ProjectionBehaviorProof,
    ProjectionProof,
)

_MODULES_ROOT = Path(__file__).resolve().parents[3]
if str(_MODULES_ROOT) not in sys.path:
    sys.path.insert(0, str(_MODULES_ROOT))

from kernel_ocg_completeness_support import (  # noqa: E402
    prove_kernel_module_ontology,
)

_CONTENT_AWARE_ROOT = Path(__file__).resolve().parents[1] / "structure" / "aware"

_CONTENT_REQUIRED_FUNCTIONS = (
    "Content.create_content",
    "Content.set_title",
    "ContentLayout.add_part_layout",
    "ContentLayout.create_content_layout_via_content",
    "ContentPart.attach_file",
    "ContentPart.create_content_part_via_content_part_content",
    "ContentPart.create_text_part_via_content_part_content",
    "ContentPartContent.create_content_part_content",
    "ContentPartContent.create_text_part_content_via_content",
    "ContentPartText.set_inline_text",
    "ContentPartText.apply_editor_patch",
    "ContentPartText.delete",
    "ContentPartText.add_segment",
    "ContentPartText.create_content_part_text_via_content_part",
    "ContentPartTextSegment.update_segment",
    "ContentPartTextSegment.delete_segment",
    "ContentPartTextSegment.add_translation",
    "ContentPartTextSegment.apply_style",
    "ContentPartTextSegment.upsert_via_content_part_text",
)

_CONTENT_CHAIN_REQUIRED_FUNCTIONS = (
    "Content.create_content",
    "Content.set_title",
    "ContentChain.build",
    "ContentChain.append_content",
    "ContentChain.append_inline_text",
    "ContentChainContent.create_content_chain_content",
    "ContentLayout.add_part_layout",
    "ContentLayout.create_content_layout_via_content",
    "ContentPart.attach_file",
    "ContentPart.create_content_part_via_content_part_content",
    "ContentPart.create_text_part_via_content_part_content",
    "ContentPartContent.create_content_part_content",
    "ContentPartContent.create_text_part_content_via_content",
    "ContentPartText.set_inline_text",
    "ContentPartText.apply_editor_patch",
    "ContentPartText.delete",
    "ContentPartText.add_segment",
    "ContentPartText.create_content_part_text_via_content_part",
    "ContentPartTextSegment.update_segment",
    "ContentPartTextSegment.delete_segment",
    "ContentPartTextSegment.add_translation",
    "ContentPartTextSegment.apply_style",
    "ContentPartTextSegment.upsert_via_content_part_text",
)

_CONTENT_DEFERRED_FUNCTIONS = (
    "ContentPartText.apply_editor_patch",
    "ContentPartText.delete",
    "ContentPartTextSegment.delete_segment",
)

_CONTENT_DOCSTRING_ONLY_FUNCTIONS = _CONTENT_DEFERRED_FUNCTIONS

_RECEIPT_GATED_REASON = (
    "covered by receipt-gated workspace local native projection proofs"
)
_DEFERRED_REASON = (
    "deferred from production-required native behavior until patch/delete "
    "FunctionImpl instructions exist"
)


@pytest.mark.asyncio
async def test_content_ontology_projection_contract_tracks_native_backlog() -> None:
    proof = await prove_kernel_module_ontology(
        "content",
        projection_proofs=(
            ProjectionProof("Content"),
            ProjectionProof("ContentChain"),
        ),
        behavior_proofs=(
            ProjectionBehaviorProof(
                "Content",
                expected_skips=_expected_skips(
                    _CONTENT_REQUIRED_FUNCTIONS,
                ),
            ),
            ProjectionBehaviorProof(
                "ContentChain",
                expected_skips=_expected_skips(
                    _CONTENT_CHAIN_REQUIRED_FUNCTIONS,
                ),
            ),
        ),
    )

    proof.assert_complete()
    report = proof.report
    assert report.status == "passed"
    assert len(report.behavior_reports) == 2
    assert report.behavior_reports[0].required_function_keys == (
        _CONTENT_REQUIRED_FUNCTIONS
    )
    assert report.behavior_reports[0].skipped_function_keys == (
        _CONTENT_REQUIRED_FUNCTIONS
    )
    assert report.behavior_reports[1].required_function_keys == (
        _CONTENT_CHAIN_REQUIRED_FUNCTIONS
    )
    assert report.behavior_reports[1].skipped_function_keys == (
        _CONTENT_CHAIN_REQUIRED_FUNCTIONS
    )
    _assert_skip_reasons(proof.behavior_results[0].function_results)
    _assert_skip_reasons(proof.behavior_results[1].function_results)
    assert proof.package_name == "content-ontology"


def test_content_native_function_sources_are_honestly_classified() -> None:
    function_bodies = _content_function_bodies_by_key()
    docstring_only_functions = tuple(
        key
        for key in sorted(function_bodies)
        if not _has_native_instruction(function_bodies[key])
    )

    assert docstring_only_functions == _CONTENT_DOCSTRING_ONLY_FUNCTIONS


def _expected_skips(
    function_keys: tuple[str, ...],
) -> tuple[FunctionCoverageSkip, ...]:
    return tuple(
        FunctionCoverageSkip(function_key, _skip_reason(function_key))
        for function_key in function_keys
    )


def _skip_reason(function_key: str) -> str:
    if function_key in _CONTENT_DEFERRED_FUNCTIONS:
        return _DEFERRED_REASON
    return _RECEIPT_GATED_REASON


def _assert_skip_reasons(function_results: object) -> None:
    reason_by_key = {result.function_key: result.reason for result in function_results}
    for function_key in _CONTENT_DEFERRED_FUNCTIONS:
        assert reason_by_key[function_key] == _DEFERRED_REASON
    for function_key, reason in reason_by_key.items():
        if function_key not in _CONTENT_DEFERRED_FUNCTIONS:
            assert reason == _RECEIPT_GATED_REASON


def _content_function_bodies_by_key() -> dict[str, str]:
    bodies: dict[str, str] = {}
    for path in sorted(_CONTENT_AWARE_ROOT.rglob("*.aware")):
        if not path.is_file():
            continue
        source = path.read_text(encoding="utf-8")
        for class_name, class_body in _aware_class_bodies(source):
            for function_name, function_body in _aware_function_bodies(class_body):
                bodies[f"{class_name}.{function_name}"] = function_body
    return bodies


def _aware_class_bodies(source: str) -> tuple[tuple[str, str], ...]:
    bodies: list[tuple[str, str]] = []
    for match in re.finditer(r"(?m)^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\b", source):
        class_name = match.group(1)
        open_brace_index = source.find("{", match.end())
        if open_brace_index == -1:
            continue
        body = _brace_body(source, open_brace_index)
        if body is not None:
            bodies.append((class_name, body))
    return tuple(bodies)


def _aware_function_bodies(source: str) -> tuple[tuple[str, str], ...]:
    bodies: list[tuple[str, str]] = []
    for match in re.finditer(r"(?m)^\s*fn\s+([A-Za-z_][A-Za-z0-9_]*)\b", source):
        function_name = match.group(1)
        open_brace_index = source.find("{", match.end())
        if open_brace_index == -1:
            continue
        body = _brace_body(source, open_brace_index)
        if body is not None:
            bodies.append((function_name, body))
    return tuple(bodies)


def _brace_body(source: str, open_brace_index: int) -> str | None:
    depth = 0
    for index in range(open_brace_index, len(source)):
        character = source[index]
        if character == "{":
            depth += 1
            continue
        if character != "}":
            continue
        depth -= 1
        if depth == 0:
            return source[open_brace_index + 1 : index]
    return None


def _has_native_instruction(function_body: str) -> bool:
    body_without_docstrings = re.sub(
        r'""".*?"""',
        "",
        function_body,
        flags=re.DOTALL,
    )
    return any(
        line.strip() and not line.strip().startswith("//")
        for line in body_without_docstrings.splitlines()
    )
