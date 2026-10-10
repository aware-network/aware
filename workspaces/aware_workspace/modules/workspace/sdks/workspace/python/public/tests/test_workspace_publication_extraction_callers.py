"""Exact caller classification for preparation, not a migration or admission.

Only Python syntax is inspected. String candidates require human disposition;
no module is imported, rewritten, selected or granted publication authority.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

import pytest
import test_workspace_publication_contract_freeze as contract

ROOT = contract.ROOT
PREFIX = contract.SDK.name
TARGET = "aware_workspace_service_sdk_adapter"
OPERATOR = PREFIX.removesuffix("_sdk") + "_operator"
LEDGER = ROOT / "docs/reports/workspace-publication-extraction-callers-20261009.json"


def mapped_module(name: str) -> str | None:
    if name == PREFIX:
        return TARGET
    if name.startswith(PREFIX + "."):
        return TARGET + name[len(PREFIX) :]
    return None


def references(source: str, prefix: str = PREFIX) -> dict[str, list[dict[str, object]]]:
    tree = ast.parse(source)
    parents = {
        child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)
    }

    def context(node: ast.AST) -> list[str]:
        result = []
        while node in parents:
            node = parents[node]
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result.append("function:" + node.name)
            elif isinstance(node, ast.If):
                result.append("if:" + ast.unparse(node.test))
            elif isinstance(node, ast.Try):
                result.append("try")
        return list(reversed(result))

    imports = []
    strings = []
    covered_lines: set[int] = set()
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [(alias.name, []) for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [(node.module, [alias.name for alias in node.names])]
        for name, members in names:
            target = mapped_module(name) if prefix == PREFIX else None
            if name == prefix or name.startswith(prefix + "."):
                imports.append(
                    {
                        "line": node.lineno,
                        "module": name,
                        "members": members,
                        "target_module": target,
                        "context": context(node),
                    }
                )
                covered_lines.update(range(node.lineno, node.end_lineno + 1))
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if prefix in value:
                target = mapped_module(value) if prefix == PREFIX else None
                module_spelling = (
                    value == prefix or value.startswith(prefix + ".")
                ) and all(part.isidentifier() for part in value.split("."))
                parent = parents.get(node)
                call = (
                    ast.unparse(parent.func) if isinstance(parent, ast.Call) else None
                )
                strings.append(
                    {
                        "line": node.lineno,
                        "value": value[:240],
                        "value_length": len(value),
                        "value_sha256": hashlib.sha256(value.encode()).hexdigest(),
                        "kind": "module_string_candidate"
                        if module_spelling
                        else "text_or_related_namespace",
                        "target_candidate": target if module_spelling else None,
                        "direct_call": call,
                        "context": context(node),
                        "disposition": "review_semantics_before_edit",
                    }
                )
                covered_lines.update(range(node.lineno, node.end_lineno + 1))
    text_lines = [
        index
        for index, line in enumerate(source.splitlines(), 1)
        if prefix in line and index not in covered_lines
    ]
    return {
        "imports": sorted(imports, key=lambda row: (row["line"], row["module"])),
        "strings": sorted(strings, key=lambda row: (row["line"], row["value"])),
        "other_text_lines": text_lines,
    }


def classify() -> dict[str, object]:
    inputs = json.loads((ROOT / contract.INPUTS).read_text())
    callers = {}
    for name, pinned in inputs["external_text_reference_candidates"].items():
        path = ROOT / name
        body = path.read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        if digest != pinned:
            raise ValueError("caller_source_changed:" + name)
        result = references(body.decode("utf-8"))
        generated = "/db/python/orm_models/" in name or "/generated/" in name
        callers[name] = {
            "sha256": digest,
            "source_kind": "generated_target" if generated else "authored",
            "disposition": "preserve_generated_target"
            if generated
            else "migrate_imports_to_service_compatibility"
            if result["imports"]
            else "review_non_import_references",
            **result,
        }
    relocations = []
    destination = contract.WORKSPACE / "sdks/workspace/service_adapter/python" / TARGET
    for record in inputs["sdk_modules"].values():
        if record["disposition"] == "rewrite_neutral_root":
            continue
        path = Path(record["source_path"])
        relocations.append(
            {
                "source_path": str(path),
                "source_sha256": record["sha256"],
                "target_path": str(destination / path.relative_to(contract.SDK)),
                "target_module": record["target_module"],
                "stage": "service_compatibility_extraction",
                "activated": False,
            }
        )
    operator_candidates = subprocess.run(
        ["rg", "-l", OPERATOR, "tools", "workspaces", "--glob", "*.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    operator_references = {}
    for name in sorted(operator_candidates):
        body = (ROOT / name).read_bytes()
        operator_references[name] = {
            "sha256": hashlib.sha256(body).hexdigest(),
            "disposition": "classify_operations_before_sdk_migration",
            **references(body.decode("utf-8"), prefix=OPERATOR),
        }
    return {
        "purpose": "publication-first-extraction-caller-classification",
        "activation_authority": False,
        "canonical_producer": str(Path(__file__).relative_to(ROOT)),
        "inputs_sha256": hashlib.sha256(
            (ROOT / contract.INPUTS).read_bytes()
        ).hexdigest(),
        "accepted_capture_sha256": hashlib.sha256(
            (
                ROOT / "docs/reports/workspace-publication-source-capture-20261009.json"
            ).read_bytes()
        ).hexdigest(),
        "caller_counts": dict(Counter(row["disposition"] for row in callers.values())),
        "callers": callers,
        "service_relocations": relocations,
        "operator_references": operator_references,
        "neutral_root_rewrite": str(contract.SDK / "__init__.py"),
        "generated_targets_are_not_admitted": True,
    }


@pytest.mark.parametrize("suffix", ["", ".client", ".features.session.state"])
def test_module_mapping_preserves_component_boundaries(suffix: str):
    assert mapped_module(PREFIX + suffix) == TARGET + suffix


@pytest.mark.parametrize("suffix", ["_local_ontology_orm_models", "_other", "x"])
def test_related_namespace_is_not_the_sdk(suffix: str):
    assert mapped_module(PREFIX + suffix) is None


def test_imports_preserve_type_checking_and_function_context():
    result = references(
        f"if TYPE_CHECKING:\n    from {PREFIX}.client import Client\n"
        f"def local():\n    import {PREFIX}.state as state\n"
    )
    assert result["imports"][0]["context"] == ["if:TYPE_CHECKING"]
    assert result["imports"][1]["context"] == ["function:local"]


def test_dynamic_import_strings_are_candidates_not_automatic_rewrites():
    result = references(f'import_module("{PREFIX}.client")\nx = "{PREFIX}_models"')
    assert result["strings"][0]["kind"] == "module_string_candidate"
    assert result["strings"][0]["direct_call"] == "import_module"
    assert result["strings"][1]["target_candidate"] is None
    assert all(
        row["disposition"] == "review_semantics_before_edit"
        for row in result["strings"]
    )


def test_comments_and_error_messages_are_not_caller_imports():
    result = references(
        f'# {PREFIX}.client\nraise ValueError("missing {PREFIX}.client")'
    )
    assert result["imports"] == []
    assert result["other_text_lines"] == [1]
    assert result["strings"][0]["kind"] == "text_or_related_namespace"


def test_ledger_reproduces_exact_current_candidate_bytes_and_syntax():
    assert classify() == json.loads(LEDGER.read_text())


def test_all_historical_candidates_have_individual_dispositions():
    ledger = classify()
    assert len(ledger["callers"]) == 109
    assert sum(ledger["caller_counts"].values()) == 109
    assert all(row["disposition"] for row in ledger["callers"].values())


def test_all_service_relocations_have_exact_unique_destination_paths():
    rows = classify()["service_relocations"]
    assert len(rows) == 172
    assert len({row["target_path"] for row in rows}) == 172
    assert all(not row["activated"] for row in rows)
    assert all(row["target_module"].startswith(TARGET + ".") for row in rows)


def test_generated_targets_remain_separate_from_authored_migration():
    rows = classify()["callers"].values()
    generated = [row for row in rows if row["source_kind"] == "generated_target"]
    assert generated
    assert all(row["disposition"] == "preserve_generated_target" for row in generated)


def test_writer_imports_are_not_mapped_directly_to_a_foreign_physical_adapter():
    result = references(f"from {OPERATOR} import run_workspace_commit", prefix=OPERATOR)
    assert result["imports"][0]["members"] == ["run_workspace_commit"]
    assert result["imports"][0]["target_module"] is None


def test_operator_reference_inventory_has_no_automatic_migration_disposition():
    rows = classify()["operator_references"].values()
    assert rows
    assert all(
        row["disposition"] == "classify_operations_before_sdk_migration" for row in rows
    )
    assert all(ref["target_module"] is None for row in rows for ref in row["imports"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--section", choices=("all", "metadata", "callers", "operator"), default="all"
    )
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--count", type=int, default=10)
    args = parser.parse_args()
    result = classify()
    if args.section == "metadata":
        result = {
            key: value
            for key, value in result.items()
            if key not in ("callers", "operator_references")
        }
    elif args.section in ("callers", "operator"):
        key = "callers" if args.section == "callers" else "operator_references"
        result = dict(list(result[key].items())[args.offset : args.offset + args.count])
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
