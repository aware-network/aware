from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.setup_language_plugins import setup_code_plugins
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.materialization import (
    LanguageMaterializationPostStepExecutionResult,
    LanguageMaterializationPostStepInput,
    LanguageMaterializationPostStepPackageContext,
    LanguageMaterializationPostStepPackageLifecycleInput,
    LanguageMaterializationPostStepPlanRequest,
    LanguageMaterializationPostStepLifecycleReconciliationRequest,
    LanguageMaterializationPostStepTargetDiscoveryRequest,
    LanguageMaterializationToolCommandRequest,
    LanguageMaterializationProducerStep,
    discover_language_materialization_post_step_targets,
    language_materialization_post_step_execution_path_hints,
    plan_language_materialization_post_steps,
    prepare_language_materialization_tool_command,
    reconcile_language_materialization_post_step_lifecycle,
    resolve_language_materialization_tool_spec,
)


@pytest.fixture
def builtin_code_language_plugins() -> Iterator[None]:
    saved_plugins = dict(CodeLanguagePluginRegistry._plugins)
    saved_supported = set(CodeLanguagePluginRegistry._supported_languages)
    CodeLanguagePluginRegistry.clear()
    setup_code_plugins()
    try:
        yield
    finally:
        CodeLanguagePluginRegistry.clear()
        CodeLanguagePluginRegistry._plugins.update(saved_plugins)
        CodeLanguagePluginRegistry._supported_languages.update(saved_supported)


def test_prepare_language_materialization_tool_command_uses_code_tool_contract(
    builtin_code_language_plugins: None,
    tmp_path: Path,
) -> None:
    _ = builtin_code_language_plugins

    prepared = prepare_language_materialization_tool_command(
        LanguageMaterializationToolCommandRequest(
            target_language_plugin_id=CodeLanguage.dart,
            tool_id="dart.format",
            cwd=tmp_path,
            targets=(Path("lib/demo.dart"),),
            args=("--fix",),
            executable_overrides={"dart": "/toolchain/dart"},
        )
    )

    assert prepared.command == (
        "/toolchain/dart",
        "format",
        "--fix",
        "lib/demo.dart",
    )
    assert prepared.tool_id == "dart.format"
    assert prepared.target_mode == "paths"
    assert prepared.mutates_targets is True


def test_prepare_language_materialization_tool_command_omits_targets_for_package_root_tools(
    builtin_code_language_plugins: None,
    tmp_path: Path,
) -> None:
    _ = builtin_code_language_plugins

    prepared = prepare_language_materialization_tool_command(
        LanguageMaterializationToolCommandRequest(
            target_language_plugin_id=CodeLanguage.dart,
            tool_id="dart.build_runner",
            cwd=tmp_path,
            targets=(tmp_path / "lib" / "device.dart",),
        )
    )

    assert prepared.command == (
        "dart",
        "run",
        "build_runner",
        "build",
        "--delete-conflicting-outputs",
    )
    assert prepared.timeout_s == 600.0
    assert prepared.target_mode == "package_root"
    assert prepared.cwd == tmp_path.resolve()


def test_prepare_language_materialization_tool_command_rejects_non_cli_tools(
    builtin_code_language_plugins: None,
    tmp_path: Path,
) -> None:
    _ = builtin_code_language_plugins

    spec = resolve_language_materialization_tool_spec(
        target_language_plugin_id=CodeLanguage.python,
        tool_id="python.format.black",
    )
    assert spec.backend == "python_api"

    with pytest.raises(ValueError, match="only CLI tools"):
        prepare_language_materialization_tool_command(
            LanguageMaterializationToolCommandRequest(
                target_language_plugin_id=CodeLanguage.python,
                tool_id="python.format.black",
                cwd=tmp_path,
                targets=(Path("demo.py"),),
            )
        )


def test_plan_language_materialization_post_steps_uses_tool_metadata_defaults(
    builtin_code_language_plugins: None,
) -> None:
    _ = builtin_code_language_plugins

    dart_plan = plan_language_materialization_post_steps(
        LanguageMaterializationPostStepPlanRequest(
            target_language_plugin_id=CodeLanguage.dart,
            has_packages=True,
        )
    )
    assert tuple(step.tool_id for step in dart_plan.steps) == (
        "dart.pub_get",
        "dart.build_runner",
        "dart.format",
    )
    assert tuple(step.source for step in dart_plan.steps) == (
        "default",
        "default",
        "default",
    )

    python_plan = plan_language_materialization_post_steps(
        LanguageMaterializationPostStepPlanRequest(
            target_language_plugin_id=CodeLanguage.python,
            has_packages=True,
        )
    )
    assert tuple(step.tool_id for step in python_plan.steps) == ("python.format.black",)


def test_plan_language_materialization_post_steps_canonicalizes_legacy_alias(
    builtin_code_language_plugins: None,
) -> None:
    _ = builtin_code_language_plugins

    plan = plan_language_materialization_post_steps(
        LanguageMaterializationPostStepPlanRequest(
            target_language_plugin_id=CodeLanguage.python,
            explicit_steps=(
                LanguageMaterializationPostStepInput(
                    name="python.black",
                    packages=("demo",),
                    on_fail="warn",
                    args=("--check",),
                ),
            ),
            has_packages=True,
        )
    )

    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.tool_id == "python.format.black"
    assert step.requested_name == "python.black"
    assert step.packages == ("demo",)
    assert step.on_fail == "warn"
    assert step.args == ("--check",)


def test_plan_language_materialization_post_steps_warns_for_missing_required_tool(
    builtin_code_language_plugins: None,
) -> None:
    _ = builtin_code_language_plugins

    plan = plan_language_materialization_post_steps(
        LanguageMaterializationPostStepPlanRequest(
            target_language_plugin_id=CodeLanguage.dart,
            explicit_steps=(
                LanguageMaterializationPostStepInput(name="dart.build_runner"),
            ),
            has_packages=True,
        )
    )

    assert tuple(step.tool_id for step in plan.steps) == ("dart.build_runner",)
    assert plan.warnings == (
        "Dart formatting is not enforced for this packaged "
        + "materialization. Add post_step name='dart.format' "
        + "(or remove explicit post_steps to use strict defaults).",
    )


def test_discover_language_materialization_post_step_targets_uses_tool_metadata(
    builtin_code_language_plugins: None,
    tmp_path: Path,
) -> None:
    _ = builtin_code_language_plugins
    package_root = tmp_path / "demo"
    lib_root = package_root / "lib"
    source = lib_root / "device.dart"
    generated = lib_root / "device.g.dart"
    readme = package_root / "README.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("class Device {}\n", encoding="utf-8")
    generated.write_text("// generated\n", encoding="utf-8")
    readme.write_text("demo\n", encoding="utf-8")

    result = discover_language_materialization_post_step_targets(
        LanguageMaterializationPostStepTargetDiscoveryRequest(
            target_language_plugin_id=CodeLanguage.dart,
            tool_id="dart.build_runner",
            package_contexts=(
                LanguageMaterializationPostStepPackageContext(
                    package_name="demo",
                    package_root=package_root,
                    package_files=(readme,),
                ),
            ),
        )
    )

    assert len(result.package_targets) == 1
    assert result.package_targets[0].target_paths == (source.resolve(),)


def test_discover_language_materialization_post_step_targets_filters_candidates(
    builtin_code_language_plugins: None,
    tmp_path: Path,
) -> None:
    _ = builtin_code_language_plugins
    python_file = tmp_path / "model.py"
    stub_file = tmp_path / "model.pyi"
    text_file = tmp_path / "model.txt"
    python_file.write_text("x=1\n", encoding="utf-8")
    stub_file.write_text("x: int\n", encoding="utf-8")
    text_file.write_text("x\n", encoding="utf-8")

    result = discover_language_materialization_post_step_targets(
        LanguageMaterializationPostStepTargetDiscoveryRequest(
            target_language_plugin_id=CodeLanguage.python,
            tool_id="python.format.black",
            candidate_paths=(python_file, stub_file, text_file),
        )
    )

    assert result.package_targets[0].target_paths == (
        python_file.resolve(),
        stub_file.resolve(),
    )


def test_post_step_execution_results_produce_lifecycle_hints(
    tmp_path: Path,
) -> None:
    formatted = tmp_path / "model.py"
    generated = tmp_path / "model.g.dart"

    hints = language_materialization_post_step_execution_path_hints(
        (
            LanguageMaterializationPostStepExecutionResult(
                tool_id="python.format.black",
                changed_paths=(formatted,),
                producer_step=LanguageMaterializationProducerStep.format_,
            ),
            LanguageMaterializationPostStepExecutionResult(
                tool_id="dart.build_runner",
                produced_paths=(generated,),
                producer_step=LanguageMaterializationProducerStep.post_step,
            ),
        )
    )

    assert hints == {
        formatted.resolve(): LanguageMaterializationProducerStep.format_,
        generated.resolve(): LanguageMaterializationProducerStep.post_step,
    }


def test_reconcile_post_step_lifecycle_tracks_effects_and_refreshed_files(
    tmp_path: Path,
) -> None:
    package_root = tmp_path / "pkg"
    source = package_root / "lib" / "device.dart"
    generated = package_root / "lib" / "device.g.dart"

    result = reconcile_language_materialization_post_step_lifecycle(
        LanguageMaterializationPostStepLifecycleReconciliationRequest(
            target_language_plugin_id=CodeLanguage.dart,
            package_contexts=(
                LanguageMaterializationPostStepPackageLifecycleInput(
                    package_name="demo",
                    package_root=package_root,
                    package_files=(source,),
                    refreshed_package_files=(source, generated),
                ),
            ),
            execution_results=(
                LanguageMaterializationPostStepExecutionResult(
                    tool_id="dart.build_runner",
                    package_name="demo",
                    package_root=package_root,
                    target_paths=(source,),
                    produced_paths=(generated,),
                    producer_step=LanguageMaterializationProducerStep.post_step,
                ),
            ),
        )
    )

    assert result.should_track_outputs is True
    assert result.package_results[0].package_files == (
        source.resolve(),
        generated.resolve(),
    )
    assert result.package_results[0].package_files_changed is True
    assert result.package_results[0].has_execution_effects is True
    assert result.package_results[0].should_track_outputs is True
    assert result.metrics["post_step_lifecycle_refreshed_package_count"] == 1
