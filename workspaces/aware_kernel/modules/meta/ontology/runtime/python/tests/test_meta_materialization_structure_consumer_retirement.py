from __future__ import annotations

from pathlib import Path

import aware_meta.materialization.code_package_sources as code_package_sources
import aware_meta.materialization.service as materialization_service


def test_meta_materialization_service_uses_meta_owned_code_source_helpers() -> None:
    parse_sources, build_namespaces = (
        materialization_service._load_meta_code_package_source_helpers()
    )

    assert (
        parse_sources
        is code_package_sources.build_parsed_file_codes_for_code_package_sources
    )
    assert (
        build_namespaces
        is code_package_sources.build_namespace_by_code_id_for_code_package
    )


def test_meta_materialization_service_has_no_structure_runtime_imports() -> None:
    service_source = Path(materialization_service.__file__).read_text(encoding="utf-8")
    helper_source = Path(code_package_sources.__file__).read_text(encoding="utf-8")

    assert "aware_structure" not in service_source
    assert "aware_structure" not in helper_source
