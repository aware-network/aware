from __future__ import annotations

import copy
import os
import shutil
import threading
from pathlib import Path

import aware_specification_fs_adapter.adapter as adapter_module
import pytest
from aware_specification_fs_adapter import (
    SpecificationFsAdapterError,
    SpecificationFsAdapterErrorKind,
    SpecificationFsSchemaResolutionContext,
    adapt_specification_fs_roots,
    close_specification_fs_adapter,
    consume_specification_fs_adaptation,
    inspect_specification_fs_profile,
    install_specification_fs_adapter,
    lower_specification_fs_closures,
)


def test_result_is_consume_once_and_close_is_idempotent(
    source_fd: int, canonical_tree, schema_bytes: bytes
) -> None:
    _, spec_root = canonical_tree
    adapter = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    result = adapt_specification_fs_roots(adapter, (spec_root,))
    assert consume_specification_fs_adaptation(adapter, result) is result
    with pytest.raises(SpecificationFsAdapterError):
        consume_specification_fs_adaptation(adapter, result)
    close_specification_fs_adapter(adapter)
    close_specification_fs_adapter(adapter)
    with pytest.raises(SpecificationFsAdapterError):
        inspect_specification_fs_profile(adapter, spec_root)


def test_adapter_and_result_copies_do_not_preserve_authority(
    source_fd: int, canonical_tree, schema_bytes: bytes
) -> None:
    _, spec_root = canonical_tree
    adapter = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    try:
        with pytest.raises(TypeError):
            copy.copy(adapter)
        result = adapt_specification_fs_roots(adapter, (spec_root,))
        with pytest.raises(SpecificationFsAdapterError):
            consume_specification_fs_adaptation(adapter, copy.copy(result))
    finally:
        close_specification_fs_adapter(adapter)


@pytest.mark.parametrize(
    ("operation", "code"),
    [
        (
            lambda: install_specification_fs_adapter(True, b"", object()),
            "invalid_installation_input",
        ),
        (
            lambda: inspect_specification_fs_profile(object(), "spec"),
            "invalid_inspection_request",
        ),
        (
            lambda: adapt_specification_fs_roots(object(), ("spec",)),
            "invalid_adaptation_request",
        ),
        (
            lambda: consume_specification_fs_adaptation(object(), object()),
            "invalid_adaptation_result",
        ),
        (lambda: close_specification_fs_adapter(object()), "invalid_close_request"),
        (
            lambda: lower_specification_fs_closures((), object()),
            "invalid_lowering_input",
        ),
    ],
)
def test_each_public_entrance_has_typed_input_failure(operation, code: str) -> None:
    with pytest.raises(SpecificationFsAdapterError) as caught:
        operation()
    assert caught.value.kind is SpecificationFsAdapterErrorKind.INPUT
    assert caught.value.code == code


def test_foreign_root_rejects_before_behavior(
    source_fd: int, schema_bytes: bytes
) -> None:
    calls: list[str] = []

    class ForeignText(str):
        def encode(self, *args, **kwargs):
            calls.append("encode")
            return super().encode(*args, **kwargs)

    adapter = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    try:
        with pytest.raises(SpecificationFsAdapterError) as caught:
            adapt_specification_fs_roots(adapter, (ForeignText("specs/example"),))
        assert caught.value.code == "invalid_adaptation_request"
        assert calls == []
    finally:
        close_specification_fs_adapter(adapter)


def test_source_descriptor_is_duplicated_and_owned(
    source_fd: int, schema_bytes: bytes
) -> None:
    adapter = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    owned_fd = adapter._base_fd
    assert owned_fd != source_fd
    close_specification_fs_adapter(adapter)
    assert os.fstat(source_fd)
    with pytest.raises(OSError):
        os.fstat(owned_fd)


def test_symlink_and_external_hardlink_fail_source_observation(
    source_fd: int, canonical_tree: tuple[Path, str], schema_bytes: bytes
) -> None:
    root, spec_root = canonical_tree
    target = root / spec_root
    adapter = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    try:
        (target / "link").symlink_to("SPEC.md")
        with pytest.raises(SpecificationFsAdapterError) as caught:
            inspect_specification_fs_profile(adapter, spec_root)
        assert caught.value.code == "source_observation_failed"
        (target / "link").unlink()
        os.link(target / "SPEC.md", root / "external-link")
        with pytest.raises(SpecificationFsAdapterError) as caught:
            inspect_specification_fs_profile(adapter, spec_root)
        assert caught.value.code == "source_observation_failed"
    finally:
        close_specification_fs_adapter(adapter)


def test_coherently_restamped_result_cannot_be_consumed(
    source_fd: int, canonical_tree: tuple[Path, str], schema_bytes: bytes
) -> None:
    _, spec_root = canonical_tree
    adapter = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    try:
        result = adapt_specification_fs_roots(adapter, (spec_root,))
        object.__setattr__(result, "adaptation_digest", "sha256:" + "9" * 64)
        with pytest.raises(SpecificationFsAdapterError) as caught:
            consume_specification_fs_adaptation(adapter, result)
        assert caught.value.code == "specification_fs_adaptation_invalid"
    finally:
        close_specification_fs_adapter(adapter)


def test_foreign_nested_scalar_rejects_before_behavior(
    source_fd: int, canonical_tree: tuple[Path, str], schema_bytes: bytes
) -> None:
    _, spec_root = canonical_tree
    calls: list[str] = []

    class ForeignText(str):
        def __eq__(self, other: object) -> bool:
            calls.append("eq")
            return super().__eq__(other)

        def encode(self, *args, **kwargs):
            calls.append("encode")
            return super().encode(*args, **kwargs)

    adapter = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    try:
        result = adapt_specification_fs_roots(adapter, (spec_root,))
        object.__setattr__(result.outcomes[0], "spec_root", ForeignText(spec_root))
        with pytest.raises(SpecificationFsAdapterError) as caught:
            consume_specification_fs_adaptation(adapter, result)
        assert caught.value.code == "specification_fs_adaptation_invalid"
        assert calls == []
    finally:
        close_specification_fs_adapter(adapter)


def test_result_cannot_cross_installations(
    source_fd: int, canonical_tree: tuple[Path, str], schema_bytes: bytes
) -> None:
    _, spec_root = canonical_tree
    first = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    second = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    try:
        result = adapt_specification_fs_roots(first, (spec_root,))
        with pytest.raises(SpecificationFsAdapterError) as caught:
            consume_specification_fs_adaptation(second, result)
        assert caught.value.code == "specification_fs_adaptation_invalid"
        assert consume_specification_fs_adaptation(first, result) is result
    finally:
        close_specification_fs_adapter(first)
        close_specification_fs_adapter(second)


def test_capacity_is_reserved_and_released(
    source_fd: int, canonical_tree: tuple[Path, str], schema_bytes: bytes
) -> None:
    _, spec_root = canonical_tree
    adapter = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    try:
        results = [
            adapt_specification_fs_roots(adapter, (spec_root,)) for _ in range(128)
        ]
        with pytest.raises(SpecificationFsAdapterError) as caught:
            adapt_specification_fs_roots(adapter, (spec_root,))
        assert caught.value.code == "adaptation_capacity_exhausted"
        consume_specification_fs_adaptation(adapter, results.pop())
        replacement = adapt_specification_fs_roots(adapter, (spec_root,))
        for result in (*results, replacement):
            consume_specification_fs_adaptation(adapter, result)
    finally:
        close_specification_fs_adapter(adapter)


def test_mixed_profile_failure_is_atomic_and_ordered(
    source_fd: int, canonical_tree: tuple[Path, str], schema_bytes: bytes
) -> None:
    root, spec_root = canonical_tree
    legacy_root = "specs/legacy"
    shutil.copytree(root / spec_root, root / legacy_root)
    (root / legacy_root / "aware.spec.toml").unlink()
    adapter = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    try:
        with pytest.raises(SpecificationFsAdapterError) as caught:
            adapt_specification_fs_roots(adapter, (spec_root, legacy_root))
        assert caught.value.code == "noncanonical_specification_profile"
        assert caught.value.spec_root == legacy_root
        assert adapter._registrations == {}
        assert adapter._reserved == 0
    finally:
        close_specification_fs_adapter(adapter)


@pytest.mark.parametrize(
    "roots",
    [
        ("/absolute",),
        ("../escape",),
        ("specs\\backslash",),
        ("specs//empty",),
        ("specs/./dot",),
        ("specs/\x7fcontrol",),
    ],
)
def test_noncanonical_root_paths_have_one_typed_failure(
    source_fd: int, schema_bytes: bytes, roots: tuple[str, ...]
) -> None:
    adapter = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    try:
        with pytest.raises(SpecificationFsAdapterError) as caught:
            adapt_specification_fs_roots(adapter, roots)
        assert caught.value.kind is SpecificationFsAdapterErrorKind.INPUT
        assert caught.value.code == "invalid_adaptation_request"
    finally:
        close_specification_fs_adapter(adapter)


def test_close_during_observation_waits_and_retires_result(
    source_fd: int,
    canonical_tree: tuple[Path, str],
    schema_bytes: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, spec_root = canonical_tree
    adapter = install_specification_fs_adapter(
        source_fd, schema_bytes, SpecificationFsSchemaResolutionContext()
    )
    entered = threading.Event()
    release = threading.Event()
    original = adapter_module.observe_root

    def delayed(*args, **kwargs):
        entered.set()
        assert release.wait(timeout=5)
        return original(*args, **kwargs)

    monkeypatch.setattr(adapter_module, "observe_root", delayed)
    failures: list[SpecificationFsAdapterError] = []

    def observe() -> None:
        try:
            inspect_specification_fs_profile(adapter, spec_root)
        except SpecificationFsAdapterError as error:
            failures.append(error)

    observer = threading.Thread(target=observe)
    closer = threading.Thread(target=close_specification_fs_adapter, args=(adapter,))
    observer.start()
    assert entered.wait(timeout=5)
    closer.start()
    assert closer.is_alive()
    release.set()
    observer.join(timeout=5)
    closer.join(timeout=5)
    assert not observer.is_alive() and not closer.is_alive()
    assert [value.code for value in failures] == ["specification_fs_adapter_closed"]
