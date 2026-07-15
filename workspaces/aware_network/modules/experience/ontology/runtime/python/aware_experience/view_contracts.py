from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from aware_code.builder import build_code_from_content
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.manifest.spec import AwarePackageKind
from aware_meta.fqn_resolver import NamespacePath
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_environment.setup_language_plugins import setup_language_plugins


@dataclass(frozen=True, slots=True)
class ExperienceViewStateModelContract:
    state_model_ref: str
    class_config_id: UUID
    source_path: str
    class_config: ClassConfig


def load_view_state_model_contracts_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    fqn_prefix: str,
    package_name: str,
) -> tuple[ExperienceViewStateModelContract, ...]:
    view_source_files = tuple(
        path
        for path in source_files
        if path.suffix == ".aware" and path.parts and path.parts[0] == "views"
    )
    if not view_source_files:
        return ()

    setup_language_plugins()

    sections_index = CodeSectionBuilderIndex()
    symbol_table = CodeSymbolTable()
    file_codes = []
    namespace_by_code_id: dict[UUID, NamespacePath] = {}
    for relpath in view_source_files:
        source_path = (package_root / relpath).resolve()
        content = source_path.read_text(encoding="utf-8")
        code = build_code_from_content(
            sections_index=sections_index,
            content=content,
            code_key=relpath.as_posix(),
            language=CodeLanguage.aware,
            symbol_table=symbol_table,
        )
        namespace_by_code_id[code.id] = NamespacePath(
            package=fqn_prefix,
            namespace=_view_namespace(relpath=relpath),
        )
        file_codes.append((relpath.as_posix(), code))

    build_result = build_object_config_graph_from_code(
        name=f"{package_name}:views",
        description=f"Experience view-state contracts for {package_name}",
        fqn_prefix=fqn_prefix,
        file_codes=sorted(file_codes, key=lambda item: item[0]),
        namespace_by_code_id=namespace_by_code_id,
        package_kind=AwarePackageKind.state,
        external_graphs=[],
    )

    source_by_namespace = {
        _view_namespace(relpath=relpath): relpath.as_posix()
        for relpath in view_source_files
    }
    contracts: list[ExperienceViewStateModelContract] = []
    for node in build_result.graph.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
            continue
        class_config = node.class_config
        class_fqn = (class_config.class_fqn or "").strip()
        if not class_fqn:
            continue
        namespace = _namespace_from_class_fqn(
            fqn_prefix=fqn_prefix,
            class_fqn=class_fqn,
        )
        contracts.append(
            ExperienceViewStateModelContract(
                state_model_ref=class_fqn,
                class_config_id=class_config.id,
                source_path=source_by_namespace.get(namespace, ""),
                class_config=class_config,
            )
        )
    return tuple(sorted(contracts, key=lambda item: item.state_model_ref.casefold()))


def _view_namespace(*, relpath: Path) -> str:
    stem_parts = relpath.with_suffix("").parts[1:]
    segments = tuple(
        part.strip().replace("-", "_") for part in stem_parts if part.strip()
    )
    return ".".join(("views", *segments)) if segments else "views"


def _namespace_from_class_fqn(*, fqn_prefix: str, class_fqn: str) -> str:
    prefix = f"{fqn_prefix}."
    if not class_fqn.startswith(prefix):
        return ""
    remainder = class_fqn[len(prefix):]
    if "." not in remainder:
        return ""
    return remainder.rsplit(".", 1)[0]


__all__ = [
    "ExperienceViewStateModelContract",
    "load_view_state_model_contracts_from_sources",
]
