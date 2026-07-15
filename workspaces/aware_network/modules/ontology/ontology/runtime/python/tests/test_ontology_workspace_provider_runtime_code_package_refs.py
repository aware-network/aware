from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from aware_code.semantic_contract_config import source_code_package_config_ref
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.runtime.invocation_engine import MetaGraphCommitReceipt
from aware_ontology.materialization import workspace_provider


@pytest.mark.asyncio
async def test_runtime_pyproject_materializes_as_code_package_ref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / "workspace"
    package_root = workspace_root / "modules" / "test_ontology"
    package_root.mkdir(parents=True)
    ontology_toml_path = package_root / "aware.ontology.toml"
    ontology_toml_path.write_text("aware_ontology = 1\n", encoding="utf-8")

    runtime_root = package_root / "runtime" / "python"
    import_root = runtime_root / "aware_test_runtime"
    import_root.mkdir(parents=True)
    (import_root / "__init__.py").write_text(
        "VALUE = 'runtime package proof'\n",
        encoding="utf-8",
    )
    (import_root / "module.py").write_text(
        "def run() -> str:\n    return VALUE\n",
        encoding="utf-8",
    )
    (runtime_root / "README.md").write_text("runtime proof\n", encoding="utf-8")
    (runtime_root / "pyproject.toml").write_text(
        "\n".join(
            (
                "[project]",
                'name = "aware-test-runtime"',
                'version = "0.1.0"',
                'readme = "README.md"',
                "",
                "[tool.hatch.build.targets.wheel]",
                'include = ["py.typed"]',
                "",
            )
        ),
        encoding="utf-8",
    )
    (runtime_root / "py.typed").write_text("", encoding="utf-8")

    observed: dict[str, object] = {}
    code_package_id = uuid4()
    object_instance_graph_commit_id = uuid4()

    async def _fake_commit_code_package_text_snapshot(
        **kwargs: object,
    ) -> object:
        observed.update(kwargs)
        return SimpleNamespace(
            code_package=SimpleNamespace(id=code_package_id),
            object_instance_graph_commit_id=object_instance_graph_commit_id,
        )

    monkeypatch.setattr(
        workspace_provider,
        "commit_code_package_text_snapshot",
        _fake_commit_code_package_text_snapshot,
    )

    source = workspace_provider._OntologyPackageSource(
        ontology_toml_path=ontology_toml_path,
        source_manifest_path=package_root / "structure" / "aware.toml",
        package_name="test-ontology",
        fqn_prefix="aware_test",
        version_number=1,
        title=None,
        description=None,
        manifest_relative_path="modules/test_ontology/structure/aware.toml",
        package_root="modules/test_ontology/structure",
        sources_root="modules/test_ontology/structure/aware",
        runtime_manifest="runtime/python/pyproject.toml",
        runtime_project_name="aware-test-runtime",
        runtime_import_root="aware_test_runtime",
    )

    snapshot = await workspace_provider._commit_ontology_runtime_code_package_snapshot(
        index=object(),
        actor_id=None,
        source=source,
        projection_hash="code-package-projection-hash",
        workspace_root=workspace_root,
    )

    assert snapshot is not None
    config_ref = source_code_package_config_ref(
        manifest_kind="pyproject_toml",
        surface="runtime",
    )
    assert observed["code_package_config_id"] == config_ref.config_id
    assert observed["projection_hash"] == "code-package-projection-hash"
    assert observed["package_name"] == "aware-test-runtime"
    assert observed["language"] == CodeLanguage.python
    assert observed["surface"] == config_ref.surface
    assert observed["manifest_kind"] == config_ref.manifest_kind
    assert observed["manifest_relative_path"] == (
        "modules/test_ontology/runtime/python/pyproject.toml"
    )
    assert observed["package_root"] == "modules/test_ontology/runtime/python"
    assert observed["sources_root"] == (
        "modules/test_ontology/runtime/python/aware_test_runtime"
    )
    assert observed["fqn_prefix"] == "aware_test_runtime"
    assert isinstance(observed["branch_id"], UUID)

    unparsed_texts = observed["unparsed_texts_by_relative_path"]
    assert isinstance(unparsed_texts, dict)
    assert sorted(unparsed_texts) == [
        "README.md",
        "aware_test_runtime/__init__.py",
        "aware_test_runtime/module.py",
        "py.typed",
        "pyproject.toml",
    ]

    assert snapshot.role == "ontology_runtime_handler_package"
    assert snapshot.code_package_id == code_package_id
    assert snapshot.object_instance_graph_commit_id == object_instance_graph_commit_id
    assert snapshot.package_name == "aware-test-runtime"
    assert snapshot.import_root == "aware_test_runtime"
    assert snapshot.language == CodeLanguage.python.value
    assert snapshot.path_count == len(unparsed_texts)

    assert snapshot.bundle_ref() == {
        "role": "ontology_runtime_handler_package",
        "source_code_package_id": code_package_id,
        "source_object_instance_graph_commit_id": object_instance_graph_commit_id,
        "package_name": "aware-test-runtime",
        "manifest_relative_path": (
            "modules/test_ontology/runtime/python/pyproject.toml"
        ),
        "package_root": "modules/test_ontology/runtime/python",
        "sources_root": "modules/test_ontology/runtime/python/aware_test_runtime",
        "import_root": "aware_test_runtime",
        "language": CodeLanguage.python.value,
        "path_count": len(unparsed_texts),
    }


@pytest.mark.asyncio
async def test_package_materialization_reuses_committed_lane_head_on_oop_noop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    projection_hash = "sha256:ontology-package"
    package_id = workspace_provider.stable_ontology_package_id(
        name="test-ontology",
        fqn_prefix="aware_test",
    )
    head_commit_id = uuid4()
    head_oig_commit_id = uuid4()

    class _NoopLane:
        binding = SimpleNamespace(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        last_commit_id = None
        last_head_commit_id = None
        last_response = MetaGraphCommitReceipt(
            status="succeeded",
            actor_id=None,
            domain_branch_id=branch_id,
            domain_projection_hash=projection_hash,
            payload=None,
            error=None,
            logs=(),
            execution_time_ms=1,
            root_object_id=package_id,
            graph_hash_pre="sha256:unchanged",
            graph_hash_post="sha256:unchanged",
            changes=workspace_provider.JsonArray([]),
            function_call_id=uuid4(),
            function_call_response_id=uuid4(),
            commit_id=None,
            object_instance_graph_commit_id=None,
            commit_action=None,
        )

        @contextmanager
        def activate(self, *, commit: bool, publish: bool):
            assert commit is True
            assert publish is False
            yield self

    lane = _NoopLane()
    observed: dict[str, object] = {}

    class _Runtime:
        def bind(
            self,
            *,
            projection: str,
            branch_id: UUID,
            actor_id: UUID | None = None,
        ) -> _NoopLane:
            observed["bind"] = {
                "projection": projection,
                "branch_id": branch_id,
                "actor_id": actor_id,
            }
            return lane

    class _FakeOntologyPackage:
        id = package_id

        @classmethod
        async def build(cls, **kwargs: object) -> "_FakeOntologyPackage":
            observed["build"] = kwargs
            return cls()

        async def attach_runtime_code_package(self, **kwargs: object) -> None:
            observed["attach_runtime_code_package"] = kwargs

    class _FakeCommitStore:
        async def head(self, *, branch_id: UUID, projection_hash: str) -> object:
            observed["head"] = {
                "branch_id": branch_id,
                "projection_hash": projection_hash,
            }
            return {
                "commit_id": str(head_commit_id),
                "object_instance_graph_commit_id": str(head_oig_commit_id),
                "graph_hash_post": "sha256:unchanged",
            }

    monkeypatch.setattr(
        workspace_provider,
        "OntologyPackage",
        _FakeOntologyPackage,
    )
    monkeypatch.setattr(workspace_provider, "FSCommitStore", _FakeCommitStore)

    source = workspace_provider._OntologyPackageSource(
        ontology_toml_path=Path("modules/test/ontology/aware.ontology.toml"),
        source_manifest_path=Path("modules/test/ontology/structure/aware.toml"),
        package_name="test-ontology",
        fqn_prefix="aware_test",
        version_number=1,
        title=None,
        description=None,
        manifest_relative_path="modules/test/ontology/structure/aware.toml",
        package_root="modules/test/ontology/structure",
        sources_root="modules/test/ontology/structure/aware",
    )
    leaf_result = SimpleNamespace(
        code_package=SimpleNamespace(id=uuid4()),
        object_config_graph_package=SimpleNamespace(id=uuid4()),
        object_config_graph_package_object_instance_graph_commit_id=uuid4(),
        object_config_graph_object_instance_graph_commit_id=uuid4(),
    )
    config_commit = workspace_provider._OntologyConfigCommitResult(
        ontology_config_id=uuid4(),
        config_commit_id=uuid4(),
        config_head_commit_id=uuid4(),
        config_object_instance_graph_commit_id=uuid4(),
        commit_perf_ms={},
    )
    runtime_snapshot = workspace_provider._OntologyRuntimeCodePackageSnapshot(
        role="ontology_runtime_handler_package",
        code_package_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
        package_name="aware-test-runtime",
        manifest_relative_path="modules/test/ontology/runtime/python/pyproject.toml",
        package_root="modules/test/ontology/runtime/python",
        sources_root="modules/test/ontology/runtime/python/aware_test_runtime",
        import_root="aware_test_runtime",
        language=CodeLanguage.python.value,
        path_count=2,
    )

    result = await workspace_provider._commit_ontology_package_snapshot(
        runtime=_Runtime(),
        index=SimpleNamespace(opg_by_hash={projection_hash: object()}),
        actor_id=None,
        branch_id=branch_id,
        projection_hash=projection_hash,
        source=source,
        leaf_result=leaf_result,
        ontology_config_commit=config_commit,
        runtime_code_package_snapshot=runtime_snapshot,
    )

    assert observed["bind"] == {
        "projection": "OntologyPackage",
        "branch_id": branch_id,
        "actor_id": None,
    }
    assert observed["head"] == {
        "branch_id": branch_id,
        "projection_hash": projection_hash,
    }
    assert "build" in observed
    assert "attach_runtime_code_package" in observed
    assert result.ontology_package_id == package_id
    assert result.package_commit_id == head_commit_id
    assert result.package_head_commit_id == head_oig_commit_id
    assert result.package_object_instance_graph_commit_id == head_oig_commit_id
