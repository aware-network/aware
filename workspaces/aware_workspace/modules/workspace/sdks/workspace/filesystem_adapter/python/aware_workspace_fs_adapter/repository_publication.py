"""Retained capture and transactions for the one original Workspace writer.

This is not a second Git writer. Captures bind exact requested postimages and
HEAD/ref observations; publication invokes the relocated original writer.
Filesystem confinement is cooperative descriptor-based observation, not a
continuous sandbox or every-write detector.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import unicodedata
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from uuid import uuid4
from weakref import WeakKeyDictionary


@dataclass(frozen=True)
class _Candidate:
    repository_ref: str
    publication_reference: str
    expected_head: str | None
    postimages_digest: str
    message_digest: str
    request: object
    postimages: tuple
    reconciliation: object = None


class _Transaction:
    """Original physical owner holder; only its issuing port recognizes it."""


@dataclass
class _TransactionState:
    capture: _Candidate
    binding: object
    lock_context: object
    lock_observation: object
    transaction_ref: str
    phase: str = "begun"
    index: object = None
    report: object = None
    cleanup_state: str = "not_attempted"
    diagnostics: tuple[str, ...] = ()
    cleanup_diagnostics: tuple[str, ...] = ()
    projection_unknown: bool = False


def _digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _identity(value):
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
        value.st_nlink,
    )


class FilesystemRepositoryCandidatePort:
    def __init__(self, *, repository_root):
        root = Path(repository_root)
        if not root.is_absolute() or root.resolve() != root:
            raise ValueError("canonical_absolute_repository_root_required")
        self._root = root
        self._identity = (root.stat().st_dev, root.stat().st_ino)
        self._captures = {}
        self._transactions = WeakKeyDictionary()

    def _git(self, *arguments, absent_ok=False, input=None):
        result = subprocess.run(
            ("git", "-C", str(self._root), *arguments),
            check=False,
            capture_output=True,
            timeout=30,
            input=input,
            env={
                key: value
                for key, value in os.environ.items()
                if not key.startswith("GIT_")
            },
        )
        if result.returncode != 0:
            if absent_ok and result.returncode == 1:
                return None
            raise ValueError(
                "repository_capture_git_refused:"
                + result.stderr.decode("utf-8", "replace")[:300]
            )
        return result.stdout.decode("utf-8").strip()

    def _head(self):
        reference = self._git("symbolic-ref", "-q", "HEAD", absent_ok=True)
        if reference is None:
            raise ValueError("repository_publication_detached_head_unsupported")
        head = self._git("rev-parse", "--verify", "--quiet", "HEAD", absent_ok=True)
        return reference, head

    def observe_publication_receipt(self, request):
        """Bounded read-only Git facts, without locks, cleanup or recovery."""
        match = re.fullmatch(
            r"git:([0-9a-fA-F]{40}|[0-9a-fA-F]{64})", request.publication_receipt_ref
        )
        if match is None or request.repository_ref != str(self._root):
            raise ValueError("workspace_receipt_coordinate_mismatch")
        value = self._root.stat()
        if (value.st_dev, value.st_ino) != self._identity:
            raise ValueError("workspace_receipt_original_repository_required")
        environment = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("GIT_")
        }
        environment["GIT_NO_REPLACE_OBJECTS"] = "1"

        def read(*arguments, input=None):
            return subprocess.run(
                ("git", "-C", str(self._root), *arguments),
                input=input,
                check=False,
                capture_output=True,
                timeout=30,
                env=environment,
            )

        top = read("rev-parse", "--show-toplevel")
        if top.returncode != 0 or top.stdout.decode("utf-8").strip() != str(self._root):
            raise ValueError("workspace_receipt_repository_top_level_mismatch")
        commit_hash = match.group(1).lower()
        objects = read(
            "cat-file",
            "--batch-check=%(objectname) %(objecttype)",
            input=(commit_hash + "\n").encode("ascii"),
        )
        if objects.returncode != 0:
            raise ValueError("workspace_receipt_object_read_unavailable")
        fields = objects.stdout.decode("ascii").strip().split()
        observation = {
            "receipt_state": "absent",
            "reachability_state": "unknown",
            "commit_hash": None,
            "diagnostics": (),
        }
        if fields == [commit_hash, "commit"]:
            observation["receipt_state"] = "present"
            observation["commit_hash"] = commit_hash
            try:
                reachable = read("merge-base", "--is-ancestor", commit_hash, "HEAD")
                if reachable.returncode in {0, 1}:
                    observation["reachability_state"] = (
                        "reachable" if reachable.returncode == 0 else "not_reachable"
                    )
                else:
                    observation["diagnostics"] = (
                        "workspace_receipt_reachability_unavailable",
                    )
            except BaseException as error:  # noqa: BLE001 - a later read failure does not erase observed object presence
                observation["diagnostics"] = (
                    "workspace_receipt_reachability:" + type(error).__name__,
                )
        elif fields == [commit_hash, "missing"]:
            observation["diagnostics"] = ("workspace_receipt_commit_absent",)
        elif len(fields) == 2 and fields[0] == commit_hash:
            observation["diagnostics"] = ("workspace_receipt_not_commit",)
        else:
            raise ValueError("workspace_receipt_object_read_malformed")
        current = self._root.stat()
        if (current.st_dev, current.st_ino) != self._identity:
            raise ValueError("workspace_receipt_repository_changed")
        return observation

    def _postimage(self, path):
        descriptors = []
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY
        try:
            directory = os.open(self._root, flags)
            descriptors.append(directory)
            root = os.fstat(directory)
            if (root.st_dev, root.st_ino) != self._identity:
                raise ValueError("repository_capture_root_changed")
            try:
                for part in PurePosixPath(path).parts[:-1]:
                    directory = os.open(part, flags, dir_fd=directory)
                    descriptors.append(directory)
                leaf = PurePosixPath(path).name
                before = os.stat(leaf, dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                return {"path": path, "state": "absent"}
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or before.st_size > 16 * 1024 * 1024
            ):
                raise ValueError("repository_capture_regular_bounded_file_required")
            descriptor = os.open(
                leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
            )
            descriptors.append(descriptor)
            opened = os.fstat(descriptor)
            if _identity(opened) != _identity(before):
                raise ValueError("repository_capture_source_changed")
            body = bytearray()
            while len(body) <= 16 * 1024 * 1024:
                chunk = os.read(descriptor, 64 * 1024)
                if not chunk:
                    break
                body.extend(chunk)
            after = os.fstat(descriptor)
            current = os.stat(leaf, dir_fd=directory, follow_symlinks=False)
            if (
                len(body) > 16 * 1024 * 1024
                or _identity(after) != _identity(before)
                or _identity(current) != _identity(after)
            ):
                raise ValueError("repository_capture_source_changed")
            return {
                "path": path,
                "state": "file",
                "sha256": _digest(body),
                "size": len(body),
                "mode": 0o100755 if after.st_mode & 0o111 else 0o100644,
                "body": bytes(body),
            }
        finally:
            cleanup_error = None
            for descriptor in reversed(descriptors):
                try:
                    os.close(descriptor)
                except BaseException as error:  # noqa: BLE001 - dispose all opened descriptors
                    cleanup_error = cleanup_error or error
            if cleanup_error is not None:
                raise ValueError(
                    "repository_capture_descriptor_cleanup_failed"
                ) from cleanup_error

    def capture_candidate(self, request):
        for path in request.target_paths:
            if (
                type(path) is not str
                or not path
                or unicodedata.normalize("NFC", path) != path
                or "\\" in path
                or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in path)
                or any(part in {"", ".", ".."} for part in path.split("/"))
            ):
                raise ValueError("repository_capture_canonical_path_required")
        if request.repository_ref != str(self._root):
            raise ValueError("repository_capture_coordinate_mismatch")
        if self._git("rev-parse", "--show-toplevel") != str(self._root):
            raise ValueError("repository_capture_top_level_mismatch")
        first_head = self._head()
        first = tuple(self._postimage(path) for path in request.target_paths)
        second = tuple(self._postimage(path) for path in request.target_paths)
        if first != second or first_head != self._head():
            raise ValueError("repository_capture_observation_changed")
        captured = _Candidate(
            str(self._root),
            first_head[0],
            first_head[1],
            _digest(
                json.dumps(
                    {
                        "profile": "workspace-postimages-v1",
                        "paths": tuple(
                            {key: value for key, value in item.items() if key != "body"}
                            for item in first
                        ),
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode()
            ),
            _digest(request.message.encode("utf-8")),
            request,
            first,
        )
        self._captures[id(captured)] = captured
        return captured

    def capture_reconciliation(self, request, reconciliation):
        initial = captured = self.capture_candidate(request)
        try:
            if (
                re.fullmatch(
                    r"git:(?:[0-9a-f]{40}|[0-9a-f]{64})",
                    reconciliation.publication_receipt_ref,
                )
                is None
                or not reconciliation.target_paths
                or len(set(reconciliation.target_paths))
                != len(reconciliation.target_paths)
                or reconciliation.expected_head != captured.expected_head
                or captured.expected_head is None
            ):
                raise ValueError("workspace_reconciliation_coordinate_mismatch")
            captured = replace(captured, reconciliation=reconciliation)
            self._validate_reconciliation(captured)
            self._captures[id(captured)] = captured
            return captured
        finally:
            # Only the final enrolled capture survives. Initial capture is not
            # an executable replacement or a publication/recovery capability.
            self._captures.pop(id(initial), None)

    def _validate_reconciliation(self, capture, *, issue_ref=None):
        """Own physical read fences; no source policy or authorization inference."""
        from . import git_writer as writer

        request = capture.reconciliation
        publication = request.publication_receipt_ref[4:]
        root = self._root.stat()
        if self._root.is_symlink() or (root.st_dev, root.st_ino) != self._identity:
            raise ValueError("workspace_reconciliation_original_repository_required")
        if (
            tuple(self._postimage(path) for path in request.target_paths)
            != capture.postimages
        ):
            raise ValueError("workspace_reconciliation_source_stale")
        if self._head() != (capture.publication_reference, request.expected_head):
            raise ValueError("workspace_reconciliation_head_stale")
        self._git("merge-base", "--is-ancestor", publication, request.expected_head)
        body = self._git("show", "-s", "--format=%B", publication)
        tags = writer._commit_trailer_values(body=body, trailer_name="Issue-Tag")
        owned = writer._commit_trailer_values(body=body, trailer_name="Owned-Paths")
        if (
            len(tags) != 1
            or (issue_ref is not None and tags != (issue_ref,))
            or len(owned) != 1
            or not set(request.target_paths).issubset(owned[0].split(","))
        ):
            raise ValueError(
                "workspace_reconciliation_publication_issue_scope_mismatch"
            )
        for item in capture.postimages:
            path = item["path"]
            published = self._git("ls-tree", "-z", publication, "--", path)
            current = self._git("ls-tree", "-z", request.expected_head, "--", path)
            if published != current:
                raise ValueError("workspace_reconciliation_published_path_advanced")
            if item["state"] == "absent":
                if current:
                    raise ValueError("workspace_reconciliation_source_stale")
            else:
                blob = self._git("hash-object", "--stdin", input=item["body"])
                expected = f"{item['mode']:o} blob {blob}\t{path}\0"
                if current != expected:
                    raise ValueError("workspace_reconciliation_source_stale")
        if self._head() != (capture.publication_reference, request.expected_head):
            raise ValueError("workspace_reconciliation_head_stale")

    def begin(self, capture, binding):
        """Acquire the original repository lock, then validate original bytes.

        No index preparation, recovery or publication occurs before Issue spend.
        Interrupted setup releases this operation's lock, never foreign files.
        """
        from . import git_writer as writer

        if self._captures.get(id(capture)) is not capture:
            raise ValueError("workspace_original_physical_capture_required")
        lock = writer._git_mutation_lock(
            repo_root=self._root,
            owner_id=binding.execution_id,
            issue_tag=None,
            command_summary="Workspace SDK repository publication",
        )
        observed = lock.__enter__()
        try:
            if self._head() != (capture.publication_reference, capture.expected_head):
                raise ValueError("workspace_publication_head_stale")
            current = tuple(self._postimage(p) for p in capture.request.target_paths)
            if current != capture.postimages:
                raise ValueError("workspace_publication_postimages_stale")
            if capture.reconciliation is not None:
                self._validate_reconciliation(capture)
            transaction = _Transaction()
            self._transactions[transaction] = _TransactionState(
                capture, binding, lock, observed, "workspace-transaction:" + uuid4().hex
            )
            return transaction
        except BaseException:
            lock.__exit__(None, None, None)
            raise

    def publish(self, transaction, claim):
        from aware_workspace_runtime.repository_publication import (
            spend_repository_physical_claim,
        )

        from . import git_writer as writer
        from .models import WorkspaceCommitReport

        state = self._transactions.get(transaction)
        if (
            state is None
            or state.phase != "begun"
            or state.capture.reconciliation is not None
        ):
            raise ValueError("workspace_original_unspent_transaction_required")
        authorization = spend_repository_physical_claim(self, transaction, claim)
        state.phase = "spent"
        binding = state.binding
        report = state.report = WorkspaceCommitReport(
            repo_root=str(self._root),
            requested_paths=list(binding.target_paths),
            owner_id=binding.execution_id,
            status="failed",
            repository_admission_ref=authorization.receipt_ref,
        )
        runner = writer._SubprocessGitRunner()
        command_log = []
        try:
            index = state.index = writer._prepare_repository_index_transaction(
                repo_root=self._root, runner=runner, report=report
            )
            # The new operation must not silently dispose or recover another
            # attempt's journal/index before or after its own admission spend.
            index.recover_foreign_transactions = False
            index.__enter__()
            writer._initialize_isolated_index(
                runner=runner,
                repo_root=self._root,
                transaction=index,
                command_log=command_log,
            )
            if (index.updated_reference, index.expected_head) != (
                capture_ref := state.capture.publication_reference,
                state.capture.expected_head,
            ):
                raise ValueError("workspace_publication_head_stale:" + capture_ref)
            # Stage the captured binary postimages, never git-add a later
            # worktree version. The one original writer publishes this index.
            for item in state.capture.postimages:
                path = item["path"]
                if item["state"] == "absent":
                    writer._run_git(
                        runner=runner,
                        repo_root=self._root,
                        args=("git", "update-index", "--force-remove", "--", path),
                        command_log=command_log,
                        environment=index.git_environment(),
                    )
                    continue
                with writer.tempfile.NamedTemporaryFile(
                    mode="wb", delete=False
                ) as handle:
                    handle.write(item["body"])
                    raw_path = Path(handle.name)
                try:
                    blob = writer._run_git(
                        runner=runner,
                        repo_root=self._root,
                        args=("git", "hash-object", "-w", str(raw_path)),
                        command_log=command_log,
                    ).stdout.strip()
                finally:
                    raw_path.unlink(missing_ok=True)
                writer._run_git(
                    runner=runner,
                    repo_root=self._root,
                    args=(
                        "git",
                        "update-index",
                        "--add",
                        "--cacheinfo",
                        f"{item['mode']:o},{blob},{path}",
                    ),
                    command_log=command_log,
                    environment=index.git_environment(),
                )
            staged = writer._git_name_list(
                runner=runner,
                repo_root=self._root,
                args=("git", "diff", "--cached", "--name-only"),
                command_log=command_log,
                environment=index.git_environment(),
            )
            writer._ensure_paths_within_requested(
                paths=staged,
                requested_paths=binding.target_paths,
                context="captured-postimages",
            )
            if not staged:
                raise ValueError("workspace_publication_no_changes")
            index.record_staged_paths(staged)
            report.staged_paths = list(staged)
            report.commit_message = (
                state.capture.request.message
                + "\n\n"
                + "Issue-Tag: "
                + authorization.issue_ref
                + "\n"
                + "Owner: "
                + binding.execution_id
                + "\n"
                + "Owned-Paths: "
                + ",".join(binding.target_paths)
                + "\n"
                + "Aware-Work-Admission: "
                + authorization.receipt_ref
            )
            report.issue_tag = authorization.issue_ref
            writer._publish_staged_transaction(
                runner=runner,
                repo_root=self._root,
                requested_paths=binding.target_paths,
                commit_message=report.commit_message,
                allow_empty=False,
                transaction=index,
                command_log=command_log,
            )
            report.status = "ok"
        except BaseException as error:  # noqa: BLE001 - retain effects after interrupted writer
            report.error = str(error) or type(error).__name__
            state.diagnostics += (type(error).__name__,)
            # Preserve the original report even if interruption follows CAS.
        finally:
            report.command_log = [list(entry) for entry in command_log]
            writer._apply_index_transaction_report(
                report=report, transaction=state.index
            )
        return report.model_dump(mode="json")

    def reconcile(self, transaction, claim):
        """Spend fresh Issue work, then use the one original atomic projection.

        No commit-tree, update-ref, git-add, writer replay or automatic foreign
        transaction recovery belongs to this operation.
        """
        from aware_workspace_runtime.repository_publication import (
            spend_repository_physical_claim,
        )

        from . import git_writer as writer
        from .models import WorkspaceCommitReport

        state = self._transactions.get(transaction)
        if (
            state is None
            or state.phase != "begun"
            or state.capture.reconciliation is None
        ):
            raise ValueError("workspace_original_reconciliation_transaction_required")
        authorization = spend_repository_physical_claim(self, transaction, claim)
        state.phase = "spent"
        request = state.capture.reconciliation
        report = state.report = WorkspaceCommitReport(
            repo_root=str(self._root),
            requested_paths=list(request.target_paths),
            owner_id=state.binding.execution_id,
            issue_tag=authorization.issue_ref,
            repository_admission_ref=authorization.receipt_ref,
            status="failed",
            commit_hash=request.publication_receipt_ref[4:],
        )
        runner = writer._SubprocessGitRunner()
        command_log = []
        try:
            self._validate_reconciliation(
                state.capture, issue_ref=authorization.issue_ref
            )
            index = state.index = writer._prepare_repository_index_transaction(
                repo_root=self._root,
                runner=runner,
                report=report,
            )
            index.recover_foreign_transactions = False
            index.__enter__()
            index.expected_head = request.expected_head
            index.updated_reference = state.capture.publication_reference
            # Foreign staging on owned paths must not be replaced merely
            # because a reachable commit exists. Require original debt or an
            # already-current entry through the original writer's validators.
            for path in request.target_paths:
                if (
                    not writer._shared_index_matches_expected_paths(
                        runner=runner,
                        repo_root=self._root,
                        expected_head=request.expected_head,
                        requested_paths=(path,),
                        command_log=command_log,
                    )
                    and writer._projection_debt_preimage(
                        runner=runner,
                        repo_root=self._root,
                        transaction=index,
                        path=path,
                        command_log=command_log,
                    )
                    is None
                ):
                    raise ValueError("workspace_reconciliation_foreign_staging:" + path)
            state.projection_unknown = True  # before an effectful return
            index.projection_error = writer._project_shared_index_atomically(
                runner=runner,
                repo_root=self._root,
                candidate_commit=request.expected_head,
                requested_paths=request.target_paths,
                transaction=index,
                command_log=command_log,
            )
            index.projection_applied = index.projection_error is None
            state.projection_unknown = False
            report.status = "ok" if index.projection_applied else "failed"
            report.error = index.projection_error
        except BaseException as error:  # noqa: BLE001 - keep unknown index effects on interruption
            report.error = str(error) or type(error).__name__
            state.diagnostics += (type(error).__name__,)
        finally:
            report.command_log = [list(entry) for entry in command_log]
            writer._apply_index_transaction_report(
                report=report, transaction=state.index
            )
        return report.model_dump(mode="json")

    def release(self, transaction):
        from . import git_writer as writer

        state = self._transactions.get(transaction)
        if state is None:
            raise ValueError("workspace_original_physical_transaction_required")
        if state.phase == "released":
            return self.observe_transaction(transaction)
        state.phase = "released"  # once-only, including interrupted disposal
        if state.index is not None:
            try:
                state.index.__exit__(None, None, None)
            except BaseException as error:  # noqa: BLE001 - continue lock disposal
                state.cleanup_diagnostics += (
                    "transaction_cleanup:" + type(error).__name__,
                )
        try:
            state.lock_context.__exit__(None, None, None)
        except BaseException as error:  # noqa: BLE001 - retain unknown release
            state.cleanup_diagnostics += ("lock_cleanup:" + type(error).__name__,)
        state.cleanup_diagnostics += state.lock_observation.diagnostics
        state.cleanup_state = "incomplete" if state.cleanup_diagnostics else "completed"
        if state.report is not None:
            writer._apply_index_transaction_report(
                report=state.report, transaction=state.index
            )
        return self.observe_transaction(transaction)

    def observe_transaction(self, transaction):
        state = self._transactions.get(transaction)
        if state is None:
            raise ValueError("workspace_original_physical_transaction_required")
        return {
            "transaction_ref": state.transaction_ref,
            "lock_release": state.lock_observation.release_state,
            "cleanup_state": state.cleanup_state,
            "diagnostics": state.diagnostics + state.cleanup_diagnostics,
            "publication_unknown": state.index.reference_effect_unknown
            if state.index
            else False,
            "projection_unknown": state.projection_unknown,
            "report": state.report.model_dump(mode="json")
            if state.report is not None
            else None,
        }


# Own-domain physical selection. Consumers cannot replace this port with a
# structural callback merely by satisfying the shape of capture_candidate.
from aware_workspace_runtime.repository_publication import _CANDIDATE_PORT_TYPES

_CANDIDATE_PORT_TYPES.add(FilesystemRepositoryCandidatePort)
