from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from aware_meta.graph.config.runtime_derivation import (
    RuntimeObjectConfigGraphDerivationResult,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph


@dataclass(frozen=True, slots=True)
class MetaSemanticDiagnostic:
    severity: str
    code: str
    message: str
    source_path: str | None = None


def collect_meta_completeness_diagnostics(
    *,
    source_graph: ObjectConfigGraph,
    runtime_derivation: RuntimeObjectConfigGraphDerivationResult,
    severity: str = "warning",
    source_path_by_code_id: Mapping[UUID, str] | None = None,
    native_function_impl_required: bool = False,
    native_function_impl_severity: str | None = None,
) -> tuple[MetaSemanticDiagnostic, ...]:
    """Collect static OCG/OPG readiness diagnostics.

    These checks intentionally sit above build validity and below module proofs:
    they report whether a valid graph is complete enough to operate through
    constructor/projection rails.
    """

    source_paths = source_path_by_code_id or {}
    runtime_graph = runtime_derivation.runtime_graph
    runtime_external_graphs = runtime_derivation.runtime_external_graphs
    diagnostics: list[MetaSemanticDiagnostic] = []
    from aware_meta.class_.config.diagnostics import (
        collect_class_constructor_completeness_diagnostics,
    )
    from aware_meta.graph.projection.diagnostics import (
        collect_projection_completeness_diagnostics,
    )

    diagnostics.extend(
        collect_class_constructor_completeness_diagnostics(
            object_config_graph=runtime_graph,
            external_graphs=runtime_external_graphs,
            severity=severity,
            source_path_by_code_id=source_paths,
        )
    )
    diagnostics.extend(
        collect_projection_completeness_diagnostics(
            source_graph=source_graph,
            object_config_graph=runtime_graph,
            external_graphs=runtime_external_graphs,
            severity=severity,
            source_path_by_code_id=source_paths,
        )
    )
    if native_function_impl_required:
        diagnostics.extend(
            _collect_native_function_impl_diagnostics(
                object_config_graph=runtime_graph,
                severity=native_function_impl_severity or severity,
                source_path_by_code_id=source_paths,
            )
        )
    return tuple(diagnostics)


def _collect_native_function_impl_diagnostics(
    *,
    object_config_graph: ObjectConfigGraph,
    severity: str,
    source_path_by_code_id: Mapping[UUID, str],
) -> tuple[MetaSemanticDiagnostic, ...]:
    diagnostics: list[MetaSemanticDiagnostic] = []
    for class_config in _class_configs(object_config_graph):
        for link in getattr(class_config, "class_config_function_configs", ()):
            if bool(getattr(link, "is_constructor", False)):
                continue
            function_config = getattr(link, "function_config", None)
            if function_config is None:
                continue
            function_impl = getattr(function_config, "function_impl", None)
            label = _function_label(class_config, function_config)
            if function_impl is None:
                diagnostics.append(
                    MetaSemanticDiagnostic(
                        severity=severity,
                        code=(
                            "aware_meta.completeness."
                            "native_function_impl_missing"
                        ),
                        message=(
                            "Native ontology mutation function has no "
                            f".aware FunctionImpl: {label}"
                        ),
                        source_path=_source_path(
                            function_config=function_config,
                            source_path_by_code_id=source_path_by_code_id,
                        ),
                    )
                )
                continue
            if _enum_value(getattr(function_impl, "kind", None)) != "instruction_body":
                diagnostics.append(
                    MetaSemanticDiagnostic(
                        severity=severity,
                        code=(
                            "aware_meta.completeness."
                            "native_function_impl_not_instruction_body"
                        ),
                        message=(
                            "Native ontology mutation function must use an "
                            f"instruction body FunctionImpl: {label}"
                        ),
                        source_path=_source_path(
                            function_config=function_config,
                            source_path_by_code_id=source_path_by_code_id,
                        ),
                    )
                )
    return tuple(diagnostics)


def _class_configs(object_config_graph: ObjectConfigGraph) -> tuple[object, ...]:
    configs: list[object] = []
    for node in getattr(object_config_graph, "object_config_graph_nodes", ()):
        class_config = getattr(node, "class_config", None)
        if class_config is not None:
            configs.append(class_config)
    return tuple(configs)


def _function_label(class_config: object, function_config: object) -> str:
    class_name = str(
        getattr(class_config, "class_fqn", None)
        or getattr(class_config, "name", None)
        or "<unknown-class>"
    )
    function_name = str(getattr(function_config, "name", None) or "<unknown>")
    return f"{class_name}.{function_name}"


def _source_path(
    *,
    function_config: object,
    source_path_by_code_id: Mapping[UUID, str],
) -> str | None:
    code_id = getattr(function_config, "code_section_function_id", None)
    if isinstance(code_id, UUID):
        return source_path_by_code_id.get(code_id)
    return None


def _enum_value(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw).strip().lower()


__all__ = [
    "MetaSemanticDiagnostic",
    "collect_meta_completeness_diagnostics",
]
