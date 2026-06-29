"""Python package-scoped code test discovery."""

from __future__ import annotations

import re
import tomllib
from collections.abc import Iterator, Mapping, Sequence
from typing import cast

from typing_extensions import override

from aware_code.language.test_discovery import (
    CodeLanguageTestDiscovery,
    CodeTestDiscoveryCode,
    CodeTestDiscoveryContext,
    CodeTestDiscoveryResult,
    CodeTestDiscoverySection,
    CodeTestFrameworkDiscoveryDescriptor,
    CodeTestUnitDiscoveryDescriptor,
)
from aware_code_ontology.code.code_section_enums import CodeSectionType


_PYTEST_FRAMEWORK = CodeTestFrameworkDiscoveryDescriptor(
    name="pytest",
    title="pytest",
    declaration_kind="manifest_or_convention",
    declaration_ref=None,
)
_UNITTEST_FRAMEWORK = CodeTestFrameworkDiscoveryDescriptor(
    name="unittest",
    title="unittest",
    declaration_kind="source_import",
    declaration_ref=None,
)
_PYTHON_CLASS_TEST_RE = re.compile(
    r"(?ms)^class\s+(?P<class_name>Test[A-Za-z0-9_]*)[^\n]*:\s*(?P<body>.*?)(?=^class\s|\Z)"
)
_PYTHON_METHOD_TEST_RE = re.compile(r"(?m)^\s+def\s+(?P<method_name>test_[A-Za-z0-9_]*)\s*\(")


class PythonCodeTestDiscovery(CodeLanguageTestDiscovery):
    """Discover pytest/unittest framework declarations and units from Code truth."""

    @override
    def discover(self, context: CodeTestDiscoveryContext) -> CodeTestDiscoveryResult:
        frameworks_by_name: dict[str, CodeTestFrameworkDiscoveryDescriptor] = {}
        units: list[CodeTestUnitDiscoveryDescriptor] = []

        if self._manifest_declares_pytest(context):
            frameworks_by_name["pytest"] = self._framework(
                _PYTEST_FRAMEWORK,
                declaration_kind="manifest",
                declaration_ref=context.manifest_relative_path,
            )

        if self._source_declares_unittest(context.codes):
            frameworks_by_name["unittest"] = self._framework(
                _UNITTEST_FRAMEWORK,
                declaration_ref="import unittest",
            )

        for code in context.codes:
            if self._has_pytest_convention_units(code):
                _ = frameworks_by_name.setdefault(
                    "pytest",
                    self._framework(
                        _PYTEST_FRAMEWORK,
                        declaration_kind="convention",
                        declaration_ref=code.relative_path,
                    ),
                )

            if "pytest" in frameworks_by_name:
                units.extend(self._discover_pytest_units(code))
            if "unittest" in frameworks_by_name:
                units.extend(self._discover_unittest_units(code))

        return CodeTestDiscoveryResult(
            frameworks=tuple(frameworks_by_name.values()),
            units=tuple(_dedupe_units(units)),
        )

    def _framework(
        self,
        descriptor: CodeTestFrameworkDiscoveryDescriptor,
        *,
        declaration_kind: str | None = None,
        declaration_ref: str | None = None,
    ) -> CodeTestFrameworkDiscoveryDescriptor:
        return CodeTestFrameworkDiscoveryDescriptor(
            name=descriptor.name,
            title=descriptor.title,
            declaration_kind=declaration_kind or descriptor.declaration_kind,
            declaration_ref=declaration_ref,
        )

    def _manifest_declares_pytest(self, context: CodeTestDiscoveryContext) -> bool:
        manifest_text = context.manifest_text or ""
        if not manifest_text.strip():
            return False

        data: Mapping[str, object]
        try:
            data = cast(Mapping[str, object], tomllib.loads(manifest_text))
        except tomllib.TOMLDecodeError:
            return "pytest" in manifest_text.casefold()

        tool = data.get("tool")
        if isinstance(tool, Mapping):
            tool_mapping = cast(Mapping[str, object], tool)
            pytest_section = tool_mapping.get("pytest")
            if isinstance(pytest_section, Mapping) and "ini_options" in pytest_section:
                return True

        return any(_is_pytest_dependency(value) for value in _iter_manifest_values(data))

    def _source_declares_unittest(self, codes: tuple[CodeTestDiscoveryCode, ...]) -> bool:
        return any(
            "import unittest" in code.content_text or "from unittest import" in code.content_text
            for code in codes
        )

    def _has_pytest_convention_units(self, code: CodeTestDiscoveryCode) -> bool:
        return _is_python_test_path(code.relative_path) and any(
            section.section_type is CodeSectionType.function and _section_name(section).startswith("test_")
            for section in code.sections
        )

    def _discover_pytest_units(self, code: CodeTestDiscoveryCode) -> Iterator[CodeTestUnitDiscoveryDescriptor]:
        if not _is_python_test_path(code.relative_path):
            return

        for section in code.sections:
            if section.section_type is CodeSectionType.function and _section_name(section).startswith("test_"):
                name = _section_name(section)
                yield CodeTestUnitDiscoveryDescriptor(
                    framework_name="pytest",
                    relative_path=code.relative_path,
                    code_section_id=section.code_section_id,
                    unit_key=f"pytest:{code.relative_path}:{section.qualname}",
                    selector=f"{code.relative_path}::{section.qualname}",
                    kind="function",
                    name=name,
                )

        sections_by_qualname = {section.qualname: section for section in code.sections}
        for class_name, method_name in _iter_test_class_methods(code.content_text):
            class_section = sections_by_qualname.get(class_name)
            if class_section is None:
                continue
            yield CodeTestUnitDiscoveryDescriptor(
                framework_name="pytest",
                relative_path=code.relative_path,
                code_section_id=class_section.code_section_id,
                unit_key=f"pytest:{code.relative_path}:{class_name}.{method_name}",
                selector=f"{code.relative_path}::{class_name}::{method_name}",
                kind="method",
                name=method_name,
            )

    def _discover_unittest_units(self, code: CodeTestDiscoveryCode) -> Iterator[CodeTestUnitDiscoveryDescriptor]:
        sections_by_qualname = {section.qualname: section for section in code.sections}
        module_name = _module_name_from_relative_path(code.relative_path)
        for class_name, method_name in _iter_test_class_methods(code.content_text):
            class_section = sections_by_qualname.get(class_name)
            if class_section is None:
                continue
            yield CodeTestUnitDiscoveryDescriptor(
                framework_name="unittest",
                relative_path=code.relative_path,
                code_section_id=class_section.code_section_id,
                unit_key=f"unittest:{module_name}.{class_name}.{method_name}",
                selector=f"{module_name}.{class_name}.{method_name}",
                kind="method",
                name=method_name,
            )


def _iter_manifest_values(value: object) -> Iterator[object]:
    if isinstance(value, Mapping):
        value_mapping = cast(Mapping[object, object], value)
        for key, child in value_mapping.items():
            yield str(key)
            yield from _iter_manifest_values(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            yield from _iter_manifest_values(child)
    else:
        yield value


def _is_pytest_dependency(value: object) -> bool:
    if not isinstance(value, str):
        return False
    value_norm = value.casefold().strip()
    return value_norm == "pytest" or value_norm.startswith(("pytest ", "pytest=", "pytest<", "pytest>", "pytest["))


def _is_python_test_path(relative_path: str) -> bool:
    path = relative_path.replace("\\", "/")
    name = path.rsplit("/", 1)[-1]
    return "/tests/" in f"/{path}" or name.startswith("test_") or name.endswith("_test.py")


def _section_name(section: CodeTestDiscoverySection) -> str:
    return (section.qualname or section.section_key).rsplit(".", 1)[-1]


def _iter_test_class_methods(content_text: str) -> Iterator[tuple[str, str]]:
    for class_match in _PYTHON_CLASS_TEST_RE.finditer(content_text):
        class_name = class_match.group("class_name")
        body = class_match.group("body")
        for method_match in _PYTHON_METHOD_TEST_RE.finditer(body):
            yield class_name, method_match.group("method_name")


def _module_name_from_relative_path(relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/")
    if normalized.endswith(".py"):
        normalized = normalized[:-3]
    return normalized.replace("/", ".")


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


__all__ = ["PythonCodeTestDiscovery"]
