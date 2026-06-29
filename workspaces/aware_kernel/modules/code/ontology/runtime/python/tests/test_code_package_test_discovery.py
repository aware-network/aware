from __future__ import annotations

from uuid import uuid4

from aware_code.language.test_discovery import (
    CodeTestDiscoveryCode,
    CodeTestDiscoveryContext,
    CodeTestDiscoverySection,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType
from dart_grammar.code_test_discovery import DartCodeTestDiscovery
from python_grammar.code_test_discovery import PythonCodeTestDiscovery


def test_python_test_discovery_resolves_pytest_function_unit() -> None:
    section_id = uuid4()
    result = PythonCodeTestDiscovery().discover(
        CodeTestDiscoveryContext(
            package_name="demo",
            language=CodeLanguage.python,
            manifest_kind="pyproject_toml",
            manifest_relative_path="pyproject.toml",
            package_root=".",
            sources_root=".",
            manifest_text='[project]\ndependencies = ["pytest>=8"]\n',
            codes=(
                CodeTestDiscoveryCode(
                    relative_path="tests/test_demo.py",
                    content_text="def test_demo():\n    assert True\n",
                    sections=(
                        CodeTestDiscoverySection(
                            code_section_id=section_id,
                            section_key="test_demo",
                            qualname="test_demo",
                            section_type=CodeSectionType.function,
                        ),
                    ),
                ),
            ),
        )
    )

    assert [framework.name for framework in result.frameworks] == ["pytest"]
    assert len(result.units) == 1
    unit = result.units[0]
    assert unit.framework_name == "pytest"
    assert unit.code_section_id == section_id
    assert unit.unit_key == "pytest:tests/test_demo.py:test_demo"
    assert unit.selector == "tests/test_demo.py::test_demo"


def test_dart_test_discovery_resolves_flutter_testwidgets_unit() -> None:
    section_id = uuid4()
    result = DartCodeTestDiscovery().discover(
        CodeTestDiscoveryContext(
            package_name="demo",
            language=CodeLanguage.dart,
            manifest_kind="pubspec_yaml",
            manifest_relative_path="pubspec.yaml",
            package_root=".",
            sources_root="lib",
            manifest_text="dev_dependencies:\n  flutter_test:\n    sdk: flutter\n",
            codes=(
                CodeTestDiscoveryCode(
                    relative_path="test/widget_test.dart",
                    content_text=(
                        "import 'package:flutter_test/flutter_test.dart';\n"
                        "void main() {\n"
                        "  testWidgets('renders home', (tester) async {});\n"
                        "}\n"
                    ),
                    sections=(
                        CodeTestDiscoverySection(
                            code_section_id=section_id,
                            section_key="main",
                            qualname="main",
                            section_type=CodeSectionType.function,
                        ),
                    ),
                ),
            ),
        )
    )

    assert [framework.name for framework in result.frameworks] == ["flutter_test"]
    assert len(result.units) == 1
    unit = result.units[0]
    assert unit.framework_name == "flutter_test"
    assert unit.code_section_id == section_id
    assert (
        unit.unit_key == "flutter_test:test/widget_test.dart:3:testWidgets:renders home"
    )
    assert unit.selector == "test/widget_test.dart::renders home"
