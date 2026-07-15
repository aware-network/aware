"""Dart package-scoped code test discovery."""

from __future__ import annotations

import re
from collections.abc import Iterator
from uuid import UUID

from typing_extensions import override

from aware_code.language.test_discovery import (
    CodeLanguageTestDiscovery,
    CodeTestDiscoveryCode,
    CodeTestDiscoveryContext,
    CodeTestDiscoveryResult,
    CodeTestFrameworkDiscoveryDescriptor,
    CodeTestUnitDiscoveryDescriptor,
)
from aware_code_ontology.code.code_section_enums import CodeSectionType


_DART_TEST_FRAMEWORK = CodeTestFrameworkDiscoveryDescriptor(
    name="dart_test",
    title="package:test",
    declaration_kind="manifest_or_convention",
    declaration_ref=None,
)
_FLUTTER_TEST_FRAMEWORK = CodeTestFrameworkDiscoveryDescriptor(
    name="flutter_test",
    title="flutter_test",
    declaration_kind="manifest_or_import",
    declaration_ref=None,
)
_DART_TEST_CALL_RE = re.compile(
    r"(?P<callee>\btestWidgets\b|\btest\b)\s*\(\s*(?P<quote>['\"])(?P<name>.*?)(?P=quote)",
    re.DOTALL,
)


class DartCodeTestDiscovery(CodeLanguageTestDiscovery):
    """Discover package:test/flutter_test framework declarations and units."""

    @override
    def discover(self, context: CodeTestDiscoveryContext) -> CodeTestDiscoveryResult:
        frameworks_by_name: dict[str, CodeTestFrameworkDiscoveryDescriptor] = {}

        if self._manifest_declares_flutter_test(context) or self._source_imports_flutter_test(context.codes):
            frameworks_by_name["flutter_test"] = self._framework(
                _FLUTTER_TEST_FRAMEWORK,
                declaration_kind="manifest_or_import",
                declaration_ref=context.manifest_relative_path,
            )

        if self._manifest_declares_dart_test(context) or self._source_imports_dart_test(context.codes):
            frameworks_by_name["dart_test"] = self._framework(
                _DART_TEST_FRAMEWORK,
                declaration_kind="manifest_or_import",
                declaration_ref=context.manifest_relative_path,
            )

        units: list[CodeTestUnitDiscoveryDescriptor] = []
        for code in context.codes:
            calls = tuple(_iter_dart_test_calls(code.content_text))
            if calls and _is_dart_test_path(code.relative_path) and not frameworks_by_name:
                frameworks_by_name["dart_test"] = self._framework(
                    _DART_TEST_FRAMEWORK,
                    declaration_kind="convention",
                    declaration_ref=code.relative_path,
                )

            for line_number, callee, name in calls:
                framework_name = self._framework_for_call(callee, frameworks_by_name)
                if framework_name is None:
                    continue
                anchor_section_id = self._anchor_section_id(code)
                if anchor_section_id is None:
                    continue
                units.append(
                    CodeTestUnitDiscoveryDescriptor(
                        framework_name=framework_name,
                        relative_path=code.relative_path,
                        code_section_id=anchor_section_id,
                        unit_key=f"{framework_name}:{code.relative_path}:{line_number}:{callee}:{name}",
                        selector=f"{code.relative_path}::{name}",
                        kind="call",
                        name=name,
                    )
                )

        return CodeTestDiscoveryResult(
            frameworks=tuple(frameworks_by_name.values()),
            units=tuple(_dedupe_units(units)),
        )

    def _framework(
        self,
        descriptor: CodeTestFrameworkDiscoveryDescriptor,
        *,
        declaration_kind: str,
        declaration_ref: str,
    ) -> CodeTestFrameworkDiscoveryDescriptor:
        return CodeTestFrameworkDiscoveryDescriptor(
            name=descriptor.name,
            title=descriptor.title,
            declaration_kind=declaration_kind,
            declaration_ref=declaration_ref,
        )

    def _manifest_declares_flutter_test(self, context: CodeTestDiscoveryContext) -> bool:
        return bool(re.search(r"(?m)^\s*flutter_test\s*:", context.manifest_text or ""))

    def _manifest_declares_dart_test(self, context: CodeTestDiscoveryContext) -> bool:
        return bool(re.search(r"(?m)^\s*test\s*:", context.manifest_text or ""))

    def _source_imports_flutter_test(self, codes: tuple[CodeTestDiscoveryCode, ...]) -> bool:
        return any("package:flutter_test/flutter_test.dart" in code.content_text for code in codes)

    def _source_imports_dart_test(self, codes: tuple[CodeTestDiscoveryCode, ...]) -> bool:
        return any("package:test/test.dart" in code.content_text for code in codes)

    def _framework_for_call(
        self,
        callee: str,
        frameworks_by_name: dict[str, CodeTestFrameworkDiscoveryDescriptor],
    ) -> str | None:
        if callee == "testWidgets" and "flutter_test" in frameworks_by_name:
            return "flutter_test"
        if "dart_test" in frameworks_by_name:
            return "dart_test"
        if "flutter_test" in frameworks_by_name:
            return "flutter_test"
        return None

    def _anchor_section_id(self, code: CodeTestDiscoveryCode) -> UUID | None:
        main_section = next(
            (
                section
                for section in code.sections
                if section.section_type is CodeSectionType.function and section.qualname == "main"
            ),
            None,
        )
        if main_section is not None:
            return main_section.code_section_id

        function_section = next(
            (section for section in code.sections if section.section_type is CodeSectionType.function),
            None,
        )
        return function_section.code_section_id if function_section is not None else None


def _iter_dart_test_calls(content_text: str) -> Iterator[tuple[int, str, str]]:
    for match in _DART_TEST_CALL_RE.finditer(content_text):
        line_number = content_text.count("\n", 0, match.start()) + 1
        yield line_number, match.group("callee"), match.group("name").strip()


def _is_dart_test_path(relative_path: str) -> bool:
    path = relative_path.replace("\\", "/")
    return path.startswith("test/") or path.endswith("_test.dart")


def _dedupe_units(
    units: list[CodeTestUnitDiscoveryDescriptor],
) -> Iterator[CodeTestUnitDiscoveryDescriptor]:
    seen: set[tuple[str, str, str]] = set()
    for unit in units:
        key = (unit.framework_name, unit.relative_path, unit.unit_key)
        if key in seen:
            continue
        seen.add(key)
        yield unit


__all__ = ["DartCodeTestDiscovery"]
