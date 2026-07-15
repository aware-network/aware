from __future__ import annotations

import difflib
import json
from pathlib import Path
from collections.abc import Mapping
from typing import cast
from uuid import UUID

from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code.section.writer import CodeSectionWriter
from aware_meta.graph.config.render.renderer_language import (
    ObjectConfigGraphRendererLanguage,
    ObjectConfigGraphRendererPolicy,
    build_renderer_empty_code,
)
from aware_meta.graph.config.render.layout_strategy import ObjectConfigGraphRenderLayoutStrategy
from aware_meta.graph.config.stable_ids_resolution import load_stable_ids_spec_for_graph
from aware_meta.graph.config.stable_ids_spec.loader import load_stable_ids_spec_from_toml_text
from aware_meta.graph.config.stable_ids_spec.spec import (
    StableIdsSpec,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from typing_extensions import override


def _toml_literal(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=True)
    raise ValueError(f"Unsupported TOML value: {value!r}")


def _toml_list(values: tuple[str, ...]) -> str:
    return "[" + ", ".join(_toml_literal(v) for v in values) + "]"


def render_aware_stable_ids_toml(*, spec: StableIdsSpec) -> str:
    """
    Emit deterministic compiler-owned TOML for stable-id formulas.
    """

    lines: list[str] = [
        "# GENERATED CODE - DO NOT MODIFY BY HAND",
        "# Canonical stable-id formula parity artifact (phase A).",
        f"version = {spec.version}",
        "",
    ]

    for ns in spec.namespaces:
        lines.append("[[namespaces]]")
        lines.append(f"name = {_toml_literal(ns.name)}")
        lines.append(f"kind = {_toml_literal(ns.kind)}")
        lines.append(f"value = {_toml_literal(ns.value)}")
        lines.append("")

    for fn in spec.functions:
        lines.append("[[functions]]")
        lines.append(f"name = {_toml_literal(fn.name)}")
        lines.append(f"namespace = {_toml_literal(fn.namespace)}")
        lines.append(f"template = {_toml_literal(fn.template)}")
        if fn.doc:
            lines.append(f"doc = {_toml_literal(fn.doc)}")
        if fn.dart_name:
            lines.append(f"dart_name = {_toml_literal(fn.dart_name)}")
        lines.append("")

        for p in fn.params:
            lines.append("[[functions.params]]")
            lines.append(f"name = {_toml_literal(p.name)}")
            lines.append(f"type = {_toml_literal(p.type)}")
            if p.optional:
                lines.append("optional = true")
            if p.default is not None:
                default_value = cast(object, p.default)
                lines.append(f"default = {_toml_literal(default_value)}")
            if p.non_empty:
                lines.append("non_empty = true")
            if p.normalize:
                lines.append(f"normalize = {_toml_list(p.normalize)}")
            lines.append("")

        for let_contract in fn.lets:
            lines.append("[[functions.lets]]")
            lines.append(f"op = {_toml_literal(let_contract.op)}")
            if let_contract.name is not None:
                lines.append(f"name = {_toml_literal(let_contract.name)}")
            if let_contract.names:
                lines.append(f"names = {_toml_list(let_contract.names)}")
            if let_contract.param is not None:
                lines.append(f"param = {_toml_literal(let_contract.param)}")
            if let_contract.params:
                lines.append(f"params = {_toml_list(let_contract.params)}")
            if let_contract.normalize:
                lines.append(f"normalize = {_toml_list(let_contract.normalize)}")
            if let_contract.default is not None:
                lines.append(f"default = {_toml_literal(let_contract.default)}")
            if let_contract.prefix is not None:
                lines.append(f"prefix = {_toml_literal(let_contract.prefix)}")
            if let_contract.sep is not None:
                lines.append(f"sep = {_toml_literal(let_contract.sep)}")
            if let_contract.unique:
                lines.append("unique = true")
            if let_contract.sort:
                lines.append("sort = true")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


class AwareStableIdsRendererLanguage(ObjectConfigGraphRendererLanguage):
    """Emit compiler-owned stable-id TOML for ontology packages."""

    def __init__(self, layout_strategy: ObjectConfigGraphRenderLayoutStrategy):
        super().__init__(layout_strategy=layout_strategy)
        self._stable_ids_spec: StableIdsSpec | None = None
        self._ownership: str = "authored"
        self._parity_policy: str = "warn"
        self._resolution_policy: str = "class_strict"
        self._warnings: list[str] = []
        self._source_graph: ObjectConfigGraph | None = None

    @property
    @override
    def language(self) -> CodeLanguage:
        return CodeLanguage.aware

    @property
    @override
    def indent(self) -> int:
        return 4

    @property
    @override
    def comment_prefix(self) -> str:
        return "#"

    @override
    def define_assemblers(self) -> None:
        return

    @override
    def set_policy(self, policy: ObjectConfigGraphRendererPolicy | None) -> None:
        if policy is None:
            self._ownership = "authored"
            self._parity_policy = "warn"
            self._resolution_policy = "class_strict"
            self._source_graph = None
            return
        ownership_mode: str | None = None
        mode: str | None = None
        resolution_mode: str | None = None
        policy_map: Mapping[str, object] | None = (
            cast(Mapping[str, object], policy) if isinstance(policy, Mapping) else None
        )
        if policy_map is not None:
            raw_ownership = policy_map.get("stable_ids_ownership")
            if raw_ownership is not None:
                ownership_mode = str(raw_ownership).strip().lower()
            source_graph = policy_map.get("stable_ids_source_graph")
            if isinstance(source_graph, ObjectConfigGraph):
                self._source_graph = source_graph
            raw = policy_map.get("stable_ids_parity_policy")
            if raw is not None:
                mode = str(raw).strip().lower()
            raw_resolution = policy_map.get("stable_ids_resolution_policy")
            if raw_resolution is not None:
                resolution_mode = str(raw_resolution).strip().lower()
        else:
            policy_obj = cast(object, policy)
            raw_ownership = cast(object | None, getattr(policy_obj, "stable_ids_ownership", None))
            if raw_ownership is not None:
                ownership_mode = str(raw_ownership).strip().lower()
            source_graph = cast(object | None, getattr(policy_obj, "stable_ids_source_graph", None))
            if isinstance(source_graph, ObjectConfigGraph):
                self._source_graph = source_graph
            raw = cast(object | None, getattr(policy_obj, "stable_ids_parity_policy", None))
            if raw is not None:
                mode = str(raw).strip().lower()
            else:
                raw_mode = cast(object | None, getattr(policy_obj, "mode", None))
                if raw_mode is not None:
                    mode = str(raw_mode).strip().lower()
            raw_resolution = cast(object | None, getattr(policy_obj, "stable_ids_resolution_policy", None))
            if raw_resolution is not None:
                resolution_mode = str(raw_resolution).strip().lower()
        if ownership_mode is not None:
            if ownership_mode not in {"authored", "compiler"}:
                raise ValueError(
                    "stable_ids_ownership must be one of: authored, compiler "
                    + f"(got {ownership_mode!r})"
                )
            self._ownership = ownership_mode
        if resolution_mode is not None:
            if resolution_mode != "class_strict":
                raise ValueError(
                    "stable_ids_resolution_policy must be class_strict "
                    + f"(got {resolution_mode!r})"
                )
            self._resolution_policy = resolution_mode
        if mode is None:
            if self._ownership == "compiler":
                self._parity_policy = "error"
            return
        if mode not in {"off", "warn", "error"}:
            raise ValueError(
                "stable_ids_parity_policy must be one of: off, warn, error "
                + f"(got {mode!r})"
            )
        self._parity_policy = mode
        if self._ownership == "compiler":
            # Compiler ownership is always fail-closed.
            self._parity_policy = "error"

    @override
    def bind_object_config_graph(self, graph: ObjectConfigGraph) -> None:
        source_graph = self._source_graph or graph
        self._stable_ids_spec = load_stable_ids_spec_for_graph(
            graph=source_graph,
            ownership=self._ownership,
            resolution_policy=self._resolution_policy,
        )

    @override
    def extra_output_paths(self) -> list[Path]:
        if self._stable_ids_spec is None:
            return []
        filename = (
            "stable_ids.toml"
            if self._ownership == "compiler"
            else "stable_ids.generated.toml"
        )
        return [Path(filename)]

    @override
    def create_empty_code(self) -> Code:
        return build_renderer_empty_code(
            language=CodeLanguage.aware,
            renderer_key=type(self).__name__,
        )

    @override
    def clear_warnings(self) -> None:
        self._warnings.clear()

    @override
    def get_warnings(self) -> list[str]:
        return list(self._warnings)

    @override
    def emit_file(
        self,
        meta_objects: list[object],
        writer: CodeSectionWriter,
        schema: str = "default",
        class_to_class_config_map: dict[UUID, ClassConfig] | None = None,
        base_class_module: str | None = None,
        base_class_name: str | None = None,
    ) -> None:
        _ = schema
        _ = class_to_class_config_map
        _ = base_class_module
        _ = base_class_name

        if meta_objects:
            return
        if self._stable_ids_spec is None:
            return

        rendered = render_aware_stable_ids_toml(spec=self._stable_ids_spec)
        output_filename = (
            "stable_ids.toml"
            if self._ownership == "compiler"
            else "stable_ids.generated.toml"
        )
        if self._parity_policy != "off":
            parity_message: str | None = None
            try:
                roundtrip = load_stable_ids_spec_from_toml_text(
                    toml_text=rendered,
                    source_label=output_filename,
                )
                if roundtrip != self._stable_ids_spec:
                    parity_message = (
                        f"{output_filename} semantic parity mismatch with stable-id source spec"
                    )
            except Exception as exc:
                parity_message = f"{output_filename} parity parse failed: {exc}"

            if parity_message is not None:
                if self._parity_policy == "error":
                    raise ValueError(parity_message)
                self._warnings.append(parity_message)
        _ = writer.token(rendered)

    @override
    def validate_existing_output(
        self,
        *,
        relative_path: Path,
        output_path: Path,
        generated_source: str,
        existing_source: str,
    ) -> None:
        if self._ownership != "compiler":
            return
        if relative_path.as_posix() != "stable_ids.toml":
            return
        if existing_source == generated_source:
            return
        if self._resolution_policy == "class_strict":
            self._warnings.append(
                "compiler-owned class_strict stable_ids.toml drift adopted; "
                + f"output={output_path}"
            )
            return
        diff = "\n".join(
            difflib.unified_diff(
                existing_source.splitlines(),
                generated_source.splitlines(),
                fromfile="stable_ids.toml (existing)",
                tofile="stable_ids.toml (generated)",
                lineterm="",
            )
        )
        raise ValueError(
            "compiler-owned stable_ids.toml drift detected; "
            + "stable ids must be compiler-derived from .aware contracts.\n"
            + f"output={output_path}\n"
            + f"{diff}"
        )


__all__ = [
    "AwareStableIdsRendererLanguage",
]
