from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pytest

from aware_code.package.schemas import CodePackageInfo
from aware_code.semantic_scope import (
    SemanticScopeMaterializationDependency,
    SemanticScopeProvider,
    SemanticScopeRegistry,
    SemanticScopeResolution,
)
from aware_code_ontology.code.code_enums import CodeLanguage


@contextmanager
def _isolated_semantic_scope_registry() -> Iterator[None]:
    SemanticScopeRegistry.clear()
    try:
        yield
    finally:
        SemanticScopeRegistry.clear()


class _FakeSemanticScopeProvider(SemanticScopeProvider):
    @property
    def provider_key(self) -> str:
        return "fake_semantic_scope"

    @property
    def scope_keys(self) -> tuple[str, ...]:
        return ("fake.semantic_scope",)

    def resolve(
        self,
        code_package: CodePackageInfo,
        *,
        workspace_root: Path,
    ) -> tuple[SemanticScopeResolution, ...]:
        del workspace_root
        manifest_kind = code_package.metadata.get("manifest_kind")
        if manifest_kind != "aware_toml":
            return ()
        return (
            SemanticScopeResolution(
                scope_key="fake.semantic_scope",
                provider_key=self.provider_key,
                payload={
                    "packageName": code_package.name,
                },
                materialization_dependencies=(
                    SemanticScopeMaterializationDependency(
                        package_name="dependency-package",
                        provider_key="aware_demo",
                        semantic_package_family="demo",
                        semantic_package_kind="demo_package",
                        semantic_package_name="dependency-package",
                        source_refs=("modules/demo/aware.toml",),
                        reason="demo dependency",
                    ),
                ),
                runtime_value={"package_name": code_package.name},
            ),
        )


class _BrokenSemanticScopeProvider(SemanticScopeProvider):
    @property
    def provider_key(self) -> str:
        return "broken_semantic_scope"

    @property
    def scope_keys(self) -> tuple[str, ...]:
        return ("broken.semantic_scope",)

    def resolve(
        self,
        code_package: CodePackageInfo,
        *,
        workspace_root: Path,
    ) -> tuple[SemanticScopeResolution, ...]:
        del workspace_root
        raise RuntimeError(f"boom:{code_package.name}")


class _UnexpectedSemanticScopeProvider(SemanticScopeProvider):
    @property
    def provider_key(self) -> str:
        return "unexpected_semantic_scope"

    @property
    def scope_keys(self) -> tuple[str, ...]:
        return ("unexpected.semantic_scope",)

    def resolve(
        self,
        code_package: CodePackageInfo,
        *,
        workspace_root: Path,
    ) -> tuple[SemanticScopeResolution, ...]:
        del code_package
        del workspace_root
        raise AssertionError("unrequested semantic scope provider should not run")


def _code_package(*, manifest_kind: str = "aware_toml") -> CodePackageInfo:
    return CodePackageInfo(
        name="demo-package",
        root_path=Path("modules/demo/structure/ontology"),
        manifest_path=Path("modules/demo/structure/ontology/aware.toml"),
        language=CodeLanguage.aware,
        metadata={"manifest_kind": manifest_kind},
    )


def test_semantic_scope_registry_registers_idempotently() -> None:
    provider = _FakeSemanticScopeProvider()
    with _isolated_semantic_scope_registry():
        SemanticScopeRegistry.register(provider)
        SemanticScopeRegistry.register(provider)

        assert SemanticScopeRegistry.get_provider_keys() == ("fake_semantic_scope",)
        assert SemanticScopeRegistry.get("fake_semantic_scope") is provider


def test_semantic_scope_registry_fails_closed_for_missing_provider() -> None:
    with _isolated_semantic_scope_registry():
        with pytest.raises(KeyError, match="No semantic scope provider registered"):
            SemanticScopeRegistry.get("missing")


def test_semantic_scope_registry_resolves_provider_scopes() -> None:
    with _isolated_semantic_scope_registry():
        SemanticScopeRegistry.register(_FakeSemanticScopeProvider())

        resolutions = SemanticScopeRegistry.resolve(
            _code_package(),
            workspace_root=Path("/tmp/workspace"),
        )

    assert len(resolutions) == 1
    resolution = resolutions[0]
    assert resolution.scope_key == "fake.semantic_scope"
    assert resolution.provider_key == "fake_semantic_scope"
    assert dict(resolution.payload) == {"packageName": "demo-package"}
    assert resolution.materialization_dependencies == (
        SemanticScopeMaterializationDependency(
            package_name="dependency-package",
            provider_key="aware_demo",
            semantic_package_family="demo",
            semantic_package_kind="demo_package",
            semantic_package_name="dependency-package",
            source_refs=("modules/demo/aware.toml",),
            reason="demo dependency",
        ),
    )
    assert resolution.runtime_value == {"package_name": "demo-package"}


def test_semantic_scope_registry_ignores_provider_failures() -> None:
    with _isolated_semantic_scope_registry():
        SemanticScopeRegistry.register(_FakeSemanticScopeProvider())
        SemanticScopeRegistry.register(_BrokenSemanticScopeProvider())

        resolutions = SemanticScopeRegistry.resolve(
            _code_package(),
            workspace_root=Path("/tmp/workspace"),
        )

    assert [
        (resolution.provider_key, resolution.scope_key) for resolution in resolutions
    ] == [("fake_semantic_scope", "fake.semantic_scope")]


def test_semantic_scope_registry_resolves_only_requested_scope_keys() -> None:
    with _isolated_semantic_scope_registry():
        SemanticScopeRegistry.register(_FakeSemanticScopeProvider())
        SemanticScopeRegistry.register(_UnexpectedSemanticScopeProvider())

        resolutions = SemanticScopeRegistry.resolve(
            _code_package(),
            workspace_root=Path("/tmp/workspace"),
            scope_keys=("fake.semantic_scope",),
        )

    assert [
        (resolution.provider_key, resolution.scope_key) for resolution in resolutions
    ] == [("fake_semantic_scope", "fake.semantic_scope")]


def test_semantic_scope_registry_resolves_only_requested_provider_keys() -> None:
    with _isolated_semantic_scope_registry():
        SemanticScopeRegistry.register(_FakeSemanticScopeProvider())
        SemanticScopeRegistry.register(_UnexpectedSemanticScopeProvider())

        resolutions = SemanticScopeRegistry.resolve(
            _code_package(),
            workspace_root=Path("/tmp/workspace"),
            provider_keys=("fake_semantic_scope",),
        )

    assert [
        (resolution.provider_key, resolution.scope_key) for resolution in resolutions
    ] == [("fake_semantic_scope", "fake.semantic_scope")]
