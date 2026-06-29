from __future__ import annotations
# pyright: reportImplicitRelativeImport=false

from pathlib import Path
import sys

import pytest

_MODULES_ROOT = Path(__file__).resolve().parents[3]
_ONTOLOGY_ROOT = Path(__file__).resolve().parents[1]
if str(_MODULES_ROOT) not in sys.path:
    sys.path.insert(0, str(_MODULES_ROOT))

from kernel_ocg_completeness_support import (  # noqa: E402
    analyze_kernel_module_ocg_completeness,
    assert_no_error_diagnostics,
)


@pytest.mark.asyncio
async def test_meta_ocg_completeness_reports_warning_debt() -> None:
    response = await analyze_kernel_module_ocg_completeness("meta")

    assert response.status == "succeeded"
    assert response.package_name == "meta-ontology"
    assert_no_error_diagnostics(response)


def test_meta_function_config_remove_generated_surface_parity() -> None:
    aware_source = (
        _ONTOLOGY_ROOT / "structure/aware/class_/class_config.aware"
    ).read_text(encoding="utf-8")
    generated_handler_source = (
        _ONTOLOGY_ROOT
        / "runtime/python/aware_meta/handlers/_generated/meta_handlers.py"
    ).read_text(encoding="utf-8")
    orm_runtime_source = (
        _ONTOLOGY_ROOT
        / "structure/python/orm_runtime/aware_meta_ontology/class_/class_config.py"
    ).read_text(encoding="utf-8")

    assert "fn remove_function_config" in aware_source
    assert "function_name=\"remove_function_config\"" in generated_handler_source
    assert "class_config__remove_function_config__handler" in generated_handler_source
    assert (
        "class_config__remove_function_config__invocation_handler"
        in generated_handler_source
    )
    assert "async def remove_function_config" in orm_runtime_source


def test_meta_generated_class_instance_create_attribute_uses_receiver_attr() -> None:
    generated_handler_source = (
        _ONTOLOGY_ROOT
        / "runtime/python/aware_meta/handlers/_generated/meta_handlers.py"
    ).read_text(encoding="utf-8")

    assert "owner_key=source_object_id" not in generated_handler_source
    assert (
        'owner_key=getattr(class_instance.source_object_id, "value", '
        "class_instance.source_object_id)"
    ) in generated_handler_source
