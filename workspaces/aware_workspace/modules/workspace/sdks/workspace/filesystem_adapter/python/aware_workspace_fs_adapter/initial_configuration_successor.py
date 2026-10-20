"""One original configuration successor; same anchor, writer and FS primitive."""

from __future__ import annotations

import configparser
import hashlib
import json
import os
import shutil
import stat
import subprocess
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import MappingProxyType
from typing import Any

from aware_workspace_sdk.initial_authoring.configuration_successor import (
    DOMAIN,
    MESSAGE,
    PREFIX,
    InitialConfigurationSuccessorRequest,
    _spend,
    validate_admission,
    validate_origin,
    validate_publication,
)
from aware_workspace_sdk.initial_authoring.values import (
    InitialConfigurationRequest,
    _canonical,
    initial_reference,
)
from aware_workspace_sdk.repository_publication.codec import (
    repository_publication_value_to_payload,
)

from .initial_authoring import (
    _DIR_FLAGS,
    _DIRECTORY,
    ConfigurationAttempt,
    _empty_original,
    _identity,
    _private,
    _projection_stat,
    _read_record,
    _root_and_metadata,
    _write_record,
    configuration_attempt,
    observe,
)

DIRECTORY = "aware-initial-configuration-successor-v1"


@contextmanager
def anchor(port):
    evidence = observe(port, _attempt=True)
    with _root_and_metadata(port) as (_, metadata, _, _):
        directory = os.open(_DIRECTORY, _DIR_FLAGS, dir_fd=metadata)
        try:
            original = os.open("configuration", _DIR_FLAGS, dir_fd=directory)
            try:
                _private(os.fstat(original), 0o700)
                claim = _read_record(original, "admission.json")
            finally:
                os.close(original)
        finally:
            os.close(directory)
    request = InitialConfigurationRequest.from_wire(claim["request"])
    with configuration_attempt(port, request) as attempt:
        if _canonical(attempt.record) != _canonical(claim):
            raise ValueError("configuration_successor_original_changed")
        result = attempt.recover()
        if result["disposition"] != "recorded":
            raise ValueError("configuration_successor_original_not_recorded")
        bundle = {
            "enrollment": evidence.to_wire(),
            "admission": claim,
            "dispatch": _read_record(attempt.directory, "dispatch.json"),
            "publication": result["publication"],
        }
        yield attempt, bundle
        if (
            _canonical(_read_record(attempt.directory, "admission.json"))
            != _canonical(claim)
            or _canonical(_read_record(attempt.directory, "dispatch.json"))
            != _canonical(bundle["dispatch"])
            or _canonical(_read_record(attempt.directory, "result.json"))
            != _canonical(bundle["publication"])
            or observe(port, _attempt=True) != evidence
        ):
            raise ValueError("configuration_successor_original_changed")


def present(port):
    with _root_and_metadata(port) as (_, metadata, _, _):
        try:
            os.stat(DIRECTORY, dir_fd=metadata, follow_symlinks=False)
            return True
        except FileNotFoundError:
            return False


@contextmanager
def sidecar(port, *, create=False):
    with _root_and_metadata(port) as (_, metadata, _, _):
        if create:
            os.mkdir(DIRECTORY, mode=0o700, dir_fd=metadata)
            os.fsync(metadata)
        directory = os.open(DIRECTORY, _DIR_FLAGS, dir_fd=metadata)
        try:
            original = os.fstat(directory)
            _private(original, 0o700)
            if not set(os.listdir(directory)).issubset(
                {
                    "admission.json",
                    "dispatch.json",
                    "result.json",
                    "projection-start.json",
                    "projection-result.json",
                }
            ):
                raise ValueError("configuration_successor_unknown_event")
            yield directory, metadata
            if _identity(
                os.stat(DIRECTORY, dir_fd=metadata, follow_symlinks=False)
            ) != _identity(original):
                raise ValueError("configuration_successor_directory_substituted")
        finally:
            os.close(directory)


def source_snapshot(port, *, allow_successor=False):
    from .git_identity import observe_initial_git_identity

    if not allow_successor and present(port):
        raise ValueError("configuration_successor_already_reserved")
    with _root_and_metadata(port) as (root, metadata, root_info, metadata_info):
        _empty_original(port, root, enrolled=True)
        fd = os.open(
            "config",
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=metadata,
        )
        try:
            info = os.fstat(fd)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or info.st_size > 16384
            ):
                raise ValueError("configuration_successor_regular_config_required")
            text = os.read(fd, 16385).decode("utf-8")
            parsed = configparser.RawConfigParser()
            parsed.read_string(text)
            if (
                set(parsed.sections()) != {"core", "user"}
                or dict(parsed["core"])
                != {
                    "repositoryformatversion": "0",
                    "filemode": "true",
                    "bare": "false",
                    "logallrefupdates": "true",
                }
                or set(parsed["user"]) != {"name", "email"}
                or parsed.defaults()
            ):
                raise ValueError("configuration_successor_foreign_git_configuration")
            attribution = observe_initial_git_identity(repository_root=str(port._root))
            if attribution["status"] != "available":
                raise ValueError("configuration_successor_attribution_unavailable")
            expected = {
                "name": parsed["user"]["name"],
                "email": parsed["user"]["email"],
            }
            if (
                attribution["author"] != expected
                or attribution["committer"] != expected
            ):
                raise ValueError(
                    "configuration_successor_explicit_local_attribution_required"
                )
            _empty_original(port, root, enrolled=True)
            if _projection_stat(info) != _projection_stat(
                os.fstat(fd)
            ) or _projection_stat(info) != _projection_stat(
                os.stat("config", dir_fd=metadata, follow_symlinks=False)
            ):
                raise ValueError("configuration_successor_git_configuration_changed")
            return {
                "repository_root": str(port._root),
                "root_identity": list(_identity(root_info)),
                "metadata_identity": list(_identity(metadata_info)),
                "git_config_stat": _projection_stat(info),
                "git_config_utf8": text,
                "git_config_sha256": "sha256:"
                + hashlib.sha256(text.encode()).hexdigest(),
                "author": attribution["author"],
                "committer": attribution["committer"],
                "selected_ref": "refs/heads/main",
                "expected_head": None,
                "index_state": "absent",
                "target_path": "aware.protocol.toml",
                "target_state": "absent",
            }
        finally:
            os.close(fd)


def observe_predecessor(port):
    with anchor(port) as (original, bundle):
        if any(
            name in os.listdir(original.parent_directory)
            for name in ("project", "goal", "membership")
        ):
            raise ValueError("configuration_successor_downstream_attempt_present")
        source = source_snapshot(port)
        return {"predecessor": bundle, "source": source}


def verify_request(port, request, *, current=False, allow_successor=True):
    if type(request) is not InitialConfigurationSuccessorRequest:
        raise ValueError("exact_configuration_successor_request_required")
    wire = request.to_wire()
    if request.execution_id != observe(port, _attempt=True).execution_id:
        raise ValueError("configuration_successor_foreign_execution")
    if current and _canonical(
        source_snapshot(port, allow_successor=allow_successor)
    ) != _canonical(wire["source"]):
        raise ValueError("configuration_successor_source_changed")
    return wire


def reserve(port, claim):
    request, binding = _spend(port, claim)
    with anchor(port) as (_, bundle):
        wire = verify_request(port, request, current=True, allow_successor=False)
        if _canonical(bundle) != _canonical(wire["predecessor"]):
            raise ValueError("configuration_successor_predecessor_changed")
        issued = datetime.now(UTC)
        body = {
            "schema_id": PREFIX + "admission.v1",
            "request": wire,
            "binding": repository_publication_value_to_payload(binding),
            "issued_at": issued.isoformat(timespec="microseconds"),
            "expires_at": (issued + timedelta(seconds=300)).isoformat(
                timespec="microseconds"
            ),
        }
        record = {
            **body,
            "admission_ref": initial_reference(DOMAIN + "admission", body),
        }
        validate_admission(record, successor=True)
        with sidecar(port, create=True) as (directory, _):
            _write_record(directory, "admission.json", record)
            verify_request(port, request, current=True)
    # Historical/sidecar resolution is finished before the final source barrier.
    # Failure retains the reservation but cannot issue a live admission.
    verify_request(port, request, current=True)
    return record


class SuccessorAttempt(ConfigurationAttempt):
    _dispatch_schema = PREFIX + "dispatch.v1"
    _publication_schema = PREFIX + "publication.v1"
    _publication_domain = DOMAIN + "publication"
    _projection_schema = PREFIX + "projection"
    _projection_domain = DOMAIN + "projection"

    def _publication_source(self):
        return (
            "aware.protocol.toml",
            self.record["request"]["configuration"]["content_utf8"].encode(),
            None,
            MESSAGE,
        )

    def require_current(self):
        request = InitialConfigurationSuccessorRequest.from_wire(self.record["request"])
        verify_request(self.port, request, current=True)

    def consume(self):
        self.require_current()
        return super().consume()

    def recover(self):
        result = super().recover()
        if result["disposition"] == "recorded":
            validate_publication(result["publication"], self.record, successor=True)
        return result

    def _verify_original_result(self, result):
        super()._verify_original_result(result)
        if result.publication_state == "published":
            source = self.record["request"]["source"]
            expected = "\0".join(
                (
                    source["author"]["name"],
                    source["author"]["email"],
                    source["committer"]["name"],
                    source["committer"]["email"],
                )
            )
            if (
                self.port._git(
                    "show",
                    "-s",
                    "--format=%an%x00%ae%x00%cn%x00%ce",
                    result.commit_hash,
                )
                != expected
            ):
                raise ValueError("configuration_successor_commit_attribution_mismatch")


@contextmanager
def attempt(port, request):
    with anchor(port) as (_, bundle), sidecar(port) as (directory, metadata):
        record = _read_record(directory, "admission.json")
        original = validate_admission(record, successor=True)
        if request is not None and _canonical(request.to_wire()) != _canonical(
            original.to_wire()
        ):
            raise ValueError("configuration_successor_request_substituted")
        verify_request(port, original)
        if _canonical(bundle) != _canonical(original.to_wire()["predecessor"]):
            raise ValueError("configuration_successor_predecessor_changed")
        manager = SuccessorAttempt(port, directory, record, metadata)
        yield manager
        if _canonical(_read_record(directory, "admission.json")) != _canonical(record):
            raise ValueError("configuration_successor_admission_changed")


def _origin_from_attempt(
    manager, enrollment, predecessor, *, current
) -> dict[str, Any]:
    recovered = manager.recover()
    if recovered["disposition"] != "recorded":
        raise ValueError("configuration_origin_publication_unavailable")
    if current:
        installed = manager.project_configuration(read_only=True)
        if installed["projection_state"] != "installed":
            raise ValueError("configuration_origin_projection_unavailable")
    intent = _read_record(manager.directory, "projection-start.json")
    projection = _read_record(manager.directory, "projection-result.json")
    content = manager.record["request"]["configuration"]["content_utf8"].encode()
    manager._verify_projection_history(projection, intent, content)
    for name in ("projection-start.json", "projection-result.json"):
        fd = os.open(
            name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=manager.directory
        )
        try:
            _private(os.fstat(fd), 0o600)
            os.fsync(fd)
        finally:
            os.close(fd)
    os.fsync(manager.directory)
    if _canonical(
        _read_record(manager.directory, "projection-start.json")
    ) != _canonical(intent) or _canonical(
        _read_record(manager.directory, "projection-result.json")
    ) != _canonical(projection):
        raise ValueError("configuration_origin_projection_changed")
    body = {
        "schema_id": "aware.workspace.initial-configuration-origin.v2",
        "kind": "initial" if predecessor is None else "successor",
        "enrollment": enrollment,
        "predecessor": predecessor,
        "effective": {
            "request": manager.record["request"],
            "admission": manager.record,
            "publication": recovered["publication"],
            "projection_intent": intent,
            "projection": projection,
        },
    }
    wire = {
        **body,
        "origin_ref": initial_reference("workspace-initial-configuration-origin", body),
    }
    validate_origin(wire)
    if current:
        # No historical recovery follows final projection/index qualification.
        manager._verify_projection(projection, intent, content)
        manager._projection_source(recovered["original_result"])
    return wire


def origin(port, *, current=False) -> dict[str, Any]:
    if present(port):
        with attempt(port, None) as manager:
            wire = manager.record["request"]
            result = _origin_from_attempt(
                manager,
                wire["predecessor"]["enrollment"],
                wire["predecessor"],
                current=current,
            )
    else:
        with anchor(port) as (manager, bundle):
            result = _origin_from_attempt(
                manager, bundle["enrollment"], None, current=current
            )
    if current:
        # All historical resolution/custody-exit work precedes the final live
        # file/index/HEAD checks. This helper only checks source, never recovers.
        effective = result["effective"]
        cls = (
            SuccessorAttempt if result["kind"] == "successor" else ConfigurationAttempt
        )
        probe = cls(port, None, effective["admission"], None)
        from aware_workspace_sdk.repository_publication.codec import (
            repository_publication_value_from_payload,
        )
        from aware_workspace_sdk.repository_publication.values import (
            WorkspaceRepositoryCommitResult,
        )

        publication = repository_publication_value_from_payload(
            WorkspaceRepositoryCommitResult, effective["publication"]["original_result"]
        )
        content = effective["request"]["configuration"]["content_utf8"].encode()
        probe._verify_projection(
            effective["projection"], effective["projection_intent"], content
        )
        probe._projection_source(publication)
    return result


def capture(port, request, wire):
    value = InitialConfigurationSuccessorRequest.from_wire(wire)
    verify_request(port, value, current=True, allow_successor=False)
    original = port.capture_initial_configuration(
        request, wire["configuration"]["content_utf8"].encode()
    )
    result = replace(
        original,
        initial_profile="initial_configuration_successor",
        initial_source_json=_canonical(wire),
    )
    port._captures.pop(id(original), None)
    port._captures[id(result)] = result
    return result


def staging_snapshot(port, capture, binding):
    wire = json.loads(capture.initial_source_json)
    request = InitialConfigurationSuccessorRequest.from_wire(wire)
    verify_request(port, request, current=True)
    content = wire["configuration"]["content_utf8"].encode()
    item = {
        "path": "aware.protocol.toml",
        "state": "file",
        "sha256": "sha256:" + hashlib.sha256(content).hexdigest(),
        "size": len(content),
        "mode": 0o100644,
        "body": content,
    }
    if (
        capture.initial_profile != "initial_configuration_successor"
        or capture.request.message != MESSAGE
        or binding.attempt_ref != request.request_ref
        or binding.execution_id != request.execution_id
        or binding.expected_head is not None
        or binding.target_paths != ("aware.protocol.toml",)
        or capture.postimages != (item,)
        or binding.postimages_digest != capture.postimages_digest
    ):
        raise ValueError("configuration_successor_capture_substituted")
    return (MappingProxyType(item),)


def verify_staged_index(port, index, runner, command_log, snapshot):
    from . import git_writer as writer

    if not index.enabled or index.transaction_index_path is None:
        raise ValueError("configuration_successor_isolated_index_required")
    value = index.transaction_index_path.lstat()
    if not stat.S_ISREG(value.st_mode) or value.st_nlink != 1:
        raise ValueError("configuration_successor_isolated_index_substituted")
    tree = writer._run_git(
        runner=runner,
        repo_root=port._root,
        args=("git", "write-tree"),
        environment=index.git_environment(),
        command_log=command_log,
    ).stdout.strip()
    item = snapshot[0]
    oid = port._git("hash-object", "--stdin", input=item["body"])
    if (
        port._git("ls-tree", "-r", "-z", tree)
        != f"100644 blob {oid}\taware.protocol.toml\0"
    ):
        raise ValueError("configuration_successor_staged_tree_mismatch")
    return tree


def attributed_runner(source):
    from . import git_writer as writer

    # The source provider has qualified this conventional, non-linked metadata
    # directory. Neither late ambient Git selection nor a per-command overlay
    # may replace that binding. Disable unqualified global/system config too.
    root = Path(source["repository_root"])
    metadata = root / ".git"
    executable = shutil.which("git")
    if executable is None:
        raise ValueError("configuration_successor_git_executable_unavailable")
    executable = str(Path(executable).resolve(strict=True))
    frozen = MappingProxyType(
        {
            **{
                key: value
                for key, value in os.environ.items()
                if not key.startswith("GIT_")
            },
            "GIT_DIR": str(metadata),
            "GIT_WORK_TREE": str(root),
            "GIT_COMMON_DIR": str(metadata),
            "GIT_OBJECT_DIRECTORY": str(metadata / "objects"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": source["author"]["name"],
            "GIT_AUTHOR_EMAIL": source["author"]["email"],
            "GIT_COMMITTER_NAME": source["committer"]["name"],
            "GIT_COMMITTER_EMAIL": source["committer"]["email"],
        }
    )

    class OriginalAttributedRunner(writer._SubprocessGitRunner):
        def run(self, *, args, cwd):
            return self.run_with_environment(args=args, cwd=cwd, environment={})

        def run_with_environment(self, *, args, cwd, environment):
            if cwd != root or not args or args[0] != "git":
                raise ValueError("configuration_successor_git_binding_substituted")
            if set(environment) - {"GIT_INDEX_FILE"}:
                raise ValueError("configuration_successor_git_environment_substituted")
            # Deliberately do not call the base adapter: it merges os.environ
            # at every command. This is still the original writer/transaction;
            # only its process adapter supplies an exact frozen environment.
            completed = subprocess.run(
                (executable, *args[1:]),
                cwd=root,
                env={**frozen, **environment},
                capture_output=True,
                text=True,
                check=False,
            )
            return writer._GitCommandResult(
                returncode=int(completed.returncode),
                stdout=completed.stdout or "",
                stderr=completed.stderr or "",
            )

    return OriginalAttributedRunner()
