from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from typing import TypeAlias, TypedDict

from aware_code.language_service.features.base import ServiceMixinBase
from aware_code.language_service.features.diagnostics_capabilities.contracts import (
    AwareDiagnostic,
    DiagnosticRangeDict,
)
from aware_code.language_service.position import Utf16PositionMapper
from aware_workspace.compiler.workspace import WorkspaceSnapshot


class LspTextEdit(TypedDict):
    range: DiagnosticRangeDict
    newText: str


LspWorkspaceChanges: TypeAlias = dict[str, list[LspTextEdit]]


class LspWorkspaceEdit(TypedDict):
    changes: LspWorkspaceChanges


class LspCodeAction(TypedDict, total=False):
    title: str
    kind: str
    diagnostics: list[AwareDiagnostic]
    isPreferred: bool
    edit: LspWorkspaceEdit


def _split_identifier_for_candidate_search(
    *,
    identifier: str,
    package_prefixes: set[str],
) -> tuple[str, str | None, str | None] | None:
    parts = [p for p in identifier.strip().split(".") if p]
    if not parts:
        return None

    name = parts[-1]
    fqn_prefix: str | None = None
    namespace_parts = parts[:-1]
    if namespace_parts and namespace_parts[0] in package_prefixes:
        fqn_prefix = namespace_parts[0]
        namespace_parts = namespace_parts[1:]

    namespace = ".".join(namespace_parts) if namespace_parts else None
    return name, namespace, fqn_prefix


class CodeActionsMixin(ServiceMixinBase, ABC):
    _snapshot: WorkspaceSnapshot | None

    def code_actions(
        self,
        *,
        uri: str,
        document_text: str,
        context_diagnostics: Sequence[AwareDiagnostic],
    ) -> list[LspCodeAction]:
        """Return LSP CodeAction[] for diagnostics-driven quick fixes (v0)."""
        _ = document_text
        self._ensure_snapshot_for_uri(uri=uri)
        actions: list[LspCodeAction] = []

        def _append_dependency_action(
            *,
            title: str,
            diag: AwareDiagnostic,
            root_toml_uri: str,
            root_toml_text: str,
            dependency_package_name: str,
            extra_changes: LspWorkspaceChanges | None = None,
            is_preferred: bool = False,
        ) -> None:
            mapper = Utf16PositionMapper(text=root_toml_text)
            end = mapper.byte_offset_to_position(len(root_toml_text.encode("utf-8")))
            insert_range: DiagnosticRangeDict = {
                "start": {"line": end.line, "character": end.character},
                "end": {"line": end.line, "character": end.character},
            }

            if root_toml_text.endswith("\n\n"):
                insert_text = f'[[dependencies]]\npackage_name = "{dependency_package_name}"\n'
            elif root_toml_text.endswith("\n"):
                insert_text = f'\n[[dependencies]]\npackage_name = "{dependency_package_name}"\n'
            else:
                insert_text = f'\n\n[[dependencies]]\npackage_name = "{dependency_package_name}"\n'

            changes: LspWorkspaceChanges = {}
            if extra_changes:
                changes.update(extra_changes)
            changes.setdefault(root_toml_uri, []).append({"range": insert_range, "newText": insert_text})

            actions.append(
                {
                    "title": title,
                    "kind": "quickfix",
                    "diagnostics": [diag],
                    "isPreferred": is_preferred,
                    "edit": {"changes": changes},
                }
            )

        for diag in context_diagnostics:
            if diag.get("source") != "aware":
                continue

            diag_code = diag.get("code")
            diag_range = diag.get("range")
            data = diag.get("data")
            suggestions_raw = data.get("suggestions") if data is not None else None
            suggestions: list[str] = []
            if isinstance(suggestions_raw, Sequence) and not isinstance(suggestions_raw, str):
                suggestions = [item for item in suggestions_raw if isinstance(item, str) and item.strip()]

            if diag_range is not None and suggestions:
                # One quick fix per suggestion (preferred = first).
                for idx, suggestion in enumerate(suggestions):
                    title = f"Change to '{suggestion}'"
                    actions.append(
                        {
                            "title": title,
                            "kind": "quickfix",
                            "diagnostics": [diag],
                            "isPreferred": idx == 0,
                            "edit": {
                                "changes": {
                                    uri: [
                                        {
                                            "range": diag_range,
                                            "newText": suggestion,
                                        }
                                    ]
                                }
                            },
                        }
                    )

            if (
                diag_code == "aware.type.class_not_found"
                and self._snapshot is not None
                and self._snapshot.context.mode == "package"
                and self._snapshot.context.env_root is not None
                and self._snapshot.context.root_package_name
                and diag_range is not None
            ):
                identifier = data.get("identifier") if data is not None else None
                if not isinstance(identifier, str) or not identifier.strip():
                    continue

                env_root = self._snapshot.context.env_root
                root_pkg_name = self._snapshot.context.root_package_name

                packages = self._workspace.environment_packages(env_root=env_root)
                root_pkg = packages.get(root_pkg_name)
                if root_pkg is None:
                    continue

                root_deps = set(root_pkg.dependencies) | {root_pkg_name}
                root_toml_uri = self._workspace.path_to_uri(root_pkg.toml_path)
                try:
                    root_toml_text = self._workspace.get_document_text(root_toml_uri)
                except Exception:
                    root_toml_text = ""

                search_ref = _split_identifier_for_candidate_search(
                    identifier=identifier,
                    package_prefixes={pkg.fqn_prefix for pkg in packages.values()},
                )
                if search_ref is None:
                    continue
                name, namespace, prefix = search_ref

                candidates = self._workspace.find_class_candidates(
                    env_root=env_root,
                    name=name,
                    namespace=namespace,
                    fqn_prefix=prefix,
                    limit=10,
                )
                if not candidates:
                    continue

                for idx, cand in enumerate(candidates):
                    accessible = cand.fqn in self._snapshot.fqn_resolver.classes_by_fqn
                    needs_dep = (not accessible) and cand.package_name and cand.package_name not in root_deps
                    needs_replace = cand.fqn != identifier.strip()

                    extra: LspWorkspaceChanges = {}
                    if needs_replace:
                        extra[uri] = [{"range": diag_range, "newText": cand.fqn}]

                    if needs_dep:
                        title = (
                            f"Add dependency '{cand.package_name}' and use '{cand.fqn}'"
                            if needs_replace
                            else f"Add dependency '{cand.package_name}'"
                        )
                        _append_dependency_action(
                            title=title,
                            diag=diag,
                            root_toml_uri=root_toml_uri,
                            root_toml_text=root_toml_text,
                            dependency_package_name=cand.package_name,
                            extra_changes=extra if extra else None,
                            is_preferred=idx == 0,
                        )
                        continue

                    if needs_replace and accessible:
                        actions.append(
                            {
                                "title": f"Use '{cand.fqn}'",
                                "kind": "quickfix",
                                "diagnostics": [diag],
                                "isPreferred": idx == 0,
                                "edit": {"changes": {uri: [{"range": diag_range, "newText": cand.fqn}]}},
                            }
                        )

        return actions
