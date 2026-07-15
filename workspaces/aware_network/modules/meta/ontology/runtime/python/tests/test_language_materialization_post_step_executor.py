from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import pytest

from aware_meta.materialization import post_step_executor
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.setup_language_plugins import setup_code_plugins
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.materialization.post_step_executor import (
    LanguageMaterializationPostStepExecutionRequest,
    execute_language_materialization_post_steps,
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


def test_meta_post_step_executor_formats_python_generated_targets(
    builtin_code_language_plugins: None,
    tmp_path: Path,
) -> None:
    _ = builtin_code_language_plugins
    output_root = tmp_path / "python"
    source = output_root / "aware_demo_ontology" / "model.py"
    ignored = output_root / "aware_demo_ontology" / "README.md"
    source.parent.mkdir(parents=True)
    source.write_text("value={'name':'demo'}\n", encoding="utf-8")
    ignored.write_text("value={'name':'demo'}\n", encoding="utf-8")

    result = execute_language_materialization_post_steps(
        LanguageMaterializationPostStepExecutionRequest(
            target_language_plugin_id=CodeLanguage.python,
            output_root=output_root,
            generated_file_paths=(source, ignored),
            package_name="aware-demo-ontology",
            materialization_source="ontology",
        )
    )

    assert source.read_text(encoding="utf-8") == ('value = {"name": "demo"}\n')
    assert ignored.read_text(encoding="utf-8") == "value={'name':'demo'}\n"
    assert len(result.execution_results) == 1
    assert result.execution_results[0].tool_id == "python.format.black"
    assert result.execution_results[0].target_paths == (source.resolve(),)
    assert result.execution_results[0].changed_paths == (source.resolve(),)
    assert result.receipts[0]["status"] == "succeeded"
    assert result.receipts[0]["backend"] == "python_api"
    assert result.receipts[0]["materialization_source"] == "ontology"
    assert result.metrics["post_step_changed_path_count"] == 1


def test_meta_post_step_executor_requires_cli_tool_state_env(
    builtin_code_language_plugins: None,
    tmp_path: Path,
) -> None:
    _ = builtin_code_language_plugins
    output_root = tmp_path / "dart"
    source = output_root / "lib" / "demo.dart"
    source.parent.mkdir(parents=True)
    source.write_text("class Demo {}\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="language_tooling_state_required"):
        execute_language_materialization_post_steps(
            LanguageMaterializationPostStepExecutionRequest(
                target_language_plugin_id=CodeLanguage.dart,
                output_root=output_root,
                generated_file_paths=(source,),
                package_name="aware-demo-ontology",
                materialization_source="ontology",
            )
        )


def test_meta_post_step_executor_applies_cli_tool_env_and_executable_override(
    builtin_code_language_plugins: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = builtin_code_language_plugins
    output_root = tmp_path / "dart"
    source = output_root / "lib" / "demo.dart"
    source.parent.mkdir(parents=True)
    source.write_text("class Demo {}\n", encoding="utf-8")
    stale_build_state = output_root / ".dart_tool" / "build" / "lock"
    stale_build_state.mkdir(parents=True)
    (stale_build_state / "build_runner.lock").write_text("", encoding="utf-8")
    reusable_build_state = output_root / ".dart_tool" / "build" / "asset_graph.json"
    reusable_build_state.parent.mkdir(parents=True, exist_ok=True)
    reusable_build_state.write_text("{}", encoding="utf-8")
    home = tmp_path / "tool-home"
    pub_cache = tmp_path / "pub-cache"
    direct_dart = tmp_path / "dart-sdk" / "bin" / "dart"
    generated = source.with_name("demo.g.dart")
    observed: list[dict[str, object]] = []

    def _fake_run(*args: object, **kwargs: object) -> SimpleNamespace:
        observed.append({"args": args, "kwargs": kwargs})
        command = args[0] if args else ()
        if "build_runner" in command:
            assert not stale_build_state.exists()
            assert reusable_build_state.is_file()
            generated.write_text("part of 'demo.dart';\n", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(post_step_executor.subprocess, "run", _fake_run)

    result = execute_language_materialization_post_steps(
        LanguageMaterializationPostStepExecutionRequest(
            target_language_plugin_id=CodeLanguage.dart,
            output_root=output_root,
            generated_file_paths=(source,),
            package_name="aware-demo-ontology",
            materialization_source="ontology",
            tool_env_by_tool_id={
                "dart.pub_get": {
                    "HOME": str(home),
                    "PUB_CACHE": str(pub_cache),
                },
                "dart.build_runner": {
                    "HOME": str(home),
                    "PUB_CACHE": str(pub_cache),
                },
                "dart.format": {
                    "HOME": str(home),
                },
            },
            executable_overrides_by_tool_id={
                "dart.pub_get": {"dart": str(direct_dart)},
                "dart.build_runner": {"dart": str(direct_dart)},
                "dart.format": {"dart": str(direct_dart)},
            },
        )
    )

    assert [receipt["tool_id"] for receipt in result.receipts] == [
        "dart.pub_get",
        "dart.build_runner",
        "dart.format",
    ]
    pub_get_call = observed[0]["kwargs"]
    build_runner_call = observed[1]["kwargs"]
    assert isinstance(pub_get_call, dict)
    assert isinstance(build_runner_call, dict)
    assert pub_get_call["env"]["HOME"] == str(home)
    assert pub_get_call["env"]["PUB_CACHE"] == str(pub_cache)
    assert pub_get_call["stdin"] is post_step_executor.subprocess.DEVNULL
    assert build_runner_call["env"]["HOME"] == str(home)
    assert build_runner_call["env"]["PUB_CACHE"] == str(pub_cache)
    assert build_runner_call["stdin"] is post_step_executor.subprocess.DEVNULL
    assert observed[0]["args"][0][0] == str(direct_dart)
    assert observed[1]["args"][0][0] == str(direct_dart)
    assert result.receipts[0]["state_env"] == {
        "HOME": str(home),
        "PUB_CACHE": str(pub_cache),
    }
    assert result.receipts[0]["executable_overrides"] == {
        "dart": str(direct_dart),
    }
    assert result.execution_results[0].produced_paths == ()
    assert result.execution_results[1].produced_paths == (generated.resolve(),)
    assert result.receipts[0]["produced_path_count"] == 0
    assert result.receipts[1]["produced_path_count"] == 1
