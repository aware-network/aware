"""Committed repository provider for shared, read-only V2 Phase eligibility.

The compatibility CLI and portable Goal SDK call this same entrance. Missing
dependency observations are represented as not_evaluated, never as satisfied.
No Issue, event, dispatch, or repository mutation occurs here.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from collections.abc import Callable, Mapping
from datetime import date
from importlib import import_module
from pathlib import Path
from typing import ClassVar, Protocol, cast, override

from aware_goal_operational_runtime import (
    GoalFrontierCurrentness,
    GoalPhaseCurrentSourceV1,
    GoalPhaseCoordinate,
    GoalPhaseEligibilityError,
    GoalPhaseNativeDocumentV2,
    GoalPhaseNativeDocumentV3,
    observe_goal_phase_eligibility,
)
from aware_goal_sdk.phase_operation import (
    GoalPhaseObserveEligibilityRequestV1,
    issue_goal_phase_eligibility_decision_ref,
)
from aware_goal_sdk.native_phase_markdown import extract_goal_phase_native_document

from .compatibility_source import (
    GitCommittedGoalCompatibilityDirectionProjector,
    GoalNativeScopeSourceError,
)


class _NativeGoalLocation(Protocol):
    location_date: str
    location_slug: str


class _NativeGoalResolver(Protocol):
    repository_root: Path
    manifest_path: Path
    manifest_sha256: str
    goal_root: str

    def resolve_goal_path(self, relative_path: str) -> _NativeGoalLocation: ...

    def match_goal_path(self, relative_path: str) -> tuple[str, str] | None: ...

    def revalidate(self) -> None: ...


class _NativeIssueRecordBinding(Protocol):
    record_key: str
    root: str
    path_template: str


class _NativeProtocolProfile(Protocol):
    record_bindings: tuple[_NativeIssueRecordBinding, ...]


class _NativeProtocolAdmissionResult(Protocol):
    filesystem_profile: _NativeProtocolProfile | None
    source_sha256: str | None


class _NativeResolverAdmission(Protocol):
    admission: _NativeProtocolAdmissionResult
    capability: object | None


class _NativeAdmit(Protocol):
    def __call__(
        self, *, repository_root: Path, manifest_path: Path
    ) -> _NativeResolverAdmission: ...


class _NativePathResolution(Protocol):
    path: Path | None


class _NativePathResolve(Protocol):
    def __call__(
        self, *, repository_root: Path, relative_path: str, field_name: str
    ) -> _NativePathResolution: ...


def _require_native_resolver(capability: object) -> _NativeGoalResolver:
    """Use Protocol's actual issuer registry; nominal/digest lookalikes refuse."""

    try:
        protocol = import_module("aware_protocol_fs_adapter")
    except ModuleNotFoundError as error:
        raise ValueError("native_protocol_adapter_unavailable") from error
    try:
        require = cast(
            Callable[[object], _NativeGoalResolver],
            getattr(protocol, "require_native_goal_resolver"),
        )
    except AttributeError as error:
        raise ValueError("native_protocol_resolver_unavailable") from error
    return require(capability)


class _NativeAdmittedIssueLocation:
    """Protocol-admitted Issue location, with Goal-owned committed verification."""

    _TEMPLATES: ClassVar[frozenset[str]] = frozenset(
        {"YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md", "fb-YYYY-MM-DD-<slug>.md"}
    )

    def __init__(self, resolver: _NativeGoalResolver) -> None:
        protocol = import_module("aware_protocol_fs_adapter")
        admit = cast(_NativeAdmit, getattr(protocol, "admit_native_goal_resolver"))
        selected = admit(
            repository_root=resolver.repository_root,
            manifest_path=resolver.manifest_path,
        )
        admission = selected.admission
        profile = admission.filesystem_profile
        if (
            selected.capability is None
            or profile is None
            or admission.source_sha256 != resolver.manifest_sha256
        ):
            raise ValueError("native_issue_admission_mismatch")
        bindings = tuple(
            item for item in profile.record_bindings if item.record_key == "issue"
        )
        if len(bindings) != 1 or bindings[0].path_template not in self._TEMPLATES:
            raise ValueError("native_issue_template_unsupported")
        self.issue_root: str = bindings[0].root
        self._template: str = bindings[0].path_template
        self._resolver: _NativeGoalResolver = resolver
        self._resolve: _NativePathResolve = cast(
            _NativePathResolve, getattr(protocol, "resolve_repository_path_at_use")
        )
        resolver.revalidate()

    def match_issue_path(self, relative_path: str) -> bool:
        if type(relative_path) is not str or not relative_path.startswith(
            self.issue_root + "/"
        ):
            return False
        tail = relative_path[len(self.issue_root) + 1 :]
        if any(part in {"", ".", ".."} for part in tail.split("/")):
            return False
        directory = (
            r"(?P<dy>[0-9]{4})/(?P<dm>[0-9]{2})/(?P<dd>[0-9]{2})/"
            if self._template.startswith("YYYY/") else ""
        )
        match = re.fullmatch(
            directory
            + r"fb-(?P<y>[0-9]{4})-(?P<m>[0-9]{2})-(?P<d>[0-9]{2})-"
            + r"(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.md",
            tail,
        )
        if match is None:
            return False
        values = match.groupdict()
        try:
            _ = date(int(values["y"]), int(values["m"]), int(values["d"]))
        except ValueError:
            return False
        return not directory or (values["dy"], values["dm"], values["dd"]) == (
            values["y"], values["m"], values["d"]
        )

    def issue_tag_for_path(self, relative_path: str) -> str:
        if not self.match_issue_path(relative_path):
            raise GoalNativeScopeSourceError(
                "issue_outside_admitted_binding",
                "Issue path does not match admitted root/template",
            )
        name = relative_path.rsplit("/", 1)[-1]
        return _issue_tag_from_name(name)

    def resolve_issue_path(self, relative_path: str) -> None:
        self._resolver.revalidate()
        if not self.match_issue_path(relative_path):
            raise GoalNativeScopeSourceError(
                "issue_outside_admitted_binding",
                "Issue path does not match admitted root/template",
            )
        root = self._resolve(
            repository_root=self._resolver.repository_root,
            relative_path=self.issue_root,
            field_name="records.issue.root",
        )
        target = self._resolve(
            repository_root=self._resolver.repository_root,
            relative_path=relative_path,
            field_name="records.issue.target",
        )
        if (
            root.path is None
            or target.path is None
            or not target.path.is_relative_to(root.path)
        ):
            raise GoalNativeScopeSourceError(
                "issue_outside_admitted_binding", "Issue path escaped admitted root"
            )
        self._resolver.revalidate()


def _issue_tag_from_name(name: str) -> str:
    match = re.fullmatch(
        r"fb-([0-9]{4}-[0-9]{2}-[0-9]{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md",
        name,
    )
    if match is None:
        raise GoalNativeScopeSourceError(
            "issue_authority_invalid", "Issue filename is invalid"
        )
    return f"fb/{match.group(1)}/{match.group(2)}"


class _GitGoalPhaseOperationReader:
    """Internal committed-source reader; not a native construction entrance."""

    def __init__(
        self,
        repository_root: Path,
        *,
        prerequisite_goal_paths: Mapping[str, str] | None = None,
    ) -> None:
        self._root: Path = repository_root.resolve(strict=True)
        self._projector: GitCommittedGoalCompatibilityDirectionProjector = (
            GitCommittedGoalCompatibilityDirectionProjector(self._root)
        )
        self._prerequisite_goal_paths: dict[str, str] = (
            {} if prerequisite_goal_paths is None else dict(prerequisite_goal_paths)
        )

    def observe_eligibility(
        self, request: GoalPhaseObserveEligibilityRequestV1
    ) -> dict[str, object]:
        if type(request) is not GoalPhaseObserveEligibilityRequestV1:
            raise TypeError("request must be exact GoalPhaseObserveEligibilityRequestV1")
        request.__post_init__()
        head = self._git_text("rev-parse", "--verify", "HEAD^{commit}")
        locator = request.source_locator_ref
        if not locator.startswith("repository-path:"):
            raise ValueError("Git provider requires repository-path source locator")
        path = locator.removeprefix("repository-path:")
        self._validate_goal_path(path, expected_goal_tag=request.goal_tag)
        blob = self._regular_goal_blob(head, path)
        source = self._git_bytes("show", f"{head}:{path}")
        goal_sha = "sha256:" + hashlib.sha256(source).hexdigest()
        if goal_sha != request.expected_goal_sha256:
            return self._refused(request, head, goal_sha, "goal_source_stale")
        try:
            document, authority = self._projector.project_committed(
                revision_ref=head,
                goal_path=path,
                expected_goal_sha256=goal_sha,
                expected_goal_blob_oid=blob,
            )
        except GoalNativeScopeSourceError as error:
            return self._refused(request, head, goal_sha, error.code)
        if (
            document.goal_tag != request.goal_tag
            or document.document_ref != request.expected_native_document_ref
        ):
            return self._refused(request, head, goal_sha, "native_document_mismatch")
        if self._primary_identity_ambiguous(head, request.goal_tag, path):
            return self._refused(request, head, goal_sha, "goal_source_ambiguous")
        coordinate = GoalPhaseCoordinate(
            request.goal_tag, request.lane_key, request.phase_key
        )
        lane = next(
            (item for item in authority.lane_authorities if item.lane_key == request.lane_key),
            None,
        )
        if lane is None:
            return self._refused(request, head, goal_sha, "lane_authority_absent")
        external_goals = {
            dependency.prerequisite.goal_tag
            for dependency in document.operational_bundle.dependencies
            if dependency.dependent == coordinate
            and dependency.prerequisite.goal_tag != request.goal_tag
        }
        if set(self._prerequisite_goal_paths) - external_goals:
            return self._refused(request, head, goal_sha, "unrelated_prerequisite_source")
        prerequisite_sources: dict[str, GoalPhaseCurrentSourceV1] = {}
        for tag, source_path in sorted(self._prerequisite_goal_paths.items()):
            try:
                self._validate_goal_path(source_path, expected_goal_tag=tag)
                source_blob = self._regular_goal_blob(head, source_path)
                source_bytes = self._git_bytes("show", f"{head}:{source_path}")
                source_sha = "sha256:" + hashlib.sha256(source_bytes).hexdigest()
                source_document, _ = self._projector.project_committed(
                    revision_ref=head,
                    goal_path=source_path,
                    expected_goal_sha256=source_sha,
                    expected_goal_blob_oid=source_blob,
                )
            except (ValueError, GoalNativeScopeSourceError):
                return self._refused(request, head, goal_sha, "prerequisite_source_unavailable")
            if (
                type(source_document) not in {GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3}
                or source_document.goal_tag != tag
            ):
                return self._refused(request, head, goal_sha, "prerequisite_source_mismatch")
            if not self._is_unique_goal_source(head, tag, source_path):
                return self._refused(request, head, goal_sha, "prerequisite_source_ambiguous")
            prerequisite_sources[tag] = GoalPhaseCurrentSourceV1(
                source_document, head
            )
        try:
            decision = observe_goal_phase_eligibility(
                document=document,
                coordinate=coordinate,
                expected_gate_digest=request.expected_gate_digest,
                global_authority=authority.global_authority,
                lane_authority=lane,
                source_revision_ref=head,
                whole_goal_currentness=GoalFrontierCurrentness.CURRENT,
                phase_currentness=GoalFrontierCurrentness.CURRENT,
                prerequisite_sources=prerequisite_sources,
            )
        except GoalPhaseEligibilityError as error:
            return self._refused(request, head, goal_sha, error.code)
        self._before_success()
        if self._git_text("rev-parse", "--verify", "HEAD^{commit}") != head:
            return self._refused(request, head, goal_sha, "repository_head_advanced")
        result: dict[str, object] = {
            "schema_id": "aware.goal.phase-operation-result.v1",
            "operation_kind": "observe_eligibility",
            "status": "observed",
            "authority_profile": "phase_native_operational_v1",
            "effect_profile": "read_only_non_authorizing",
            "event_effect": "none",
            "dispatch_effect": "none",
            "source_locator_ref": locator,
            "coordinate": {
                "goal_tag": request.goal_tag,
                "lane_key": request.lane_key,
                "phase_key": request.phase_key,
            },
            "source_revision_ref": head,
            "source_identity_ref": "git-blob:" + blob,
            "goal_sha256": goal_sha,
            **decision.to_wire(),
        }
        result["decision_ref"] = issue_goal_phase_eligibility_decision_ref(result)
        return result

    def _validate_goal_path(self, path: str, *, expected_goal_tag: str) -> None:
        del expected_goal_tag  # Legacy compatibility has no admitted template.
        if (
            type(path) is not str
            or not path.startswith("docs/goals/") or not path.endswith(".md")
            or any(part in {"", ".", ".."} for part in path.split("/"))
            or any(character in path for character in ("\\", ":", "\n", "\r"))
        ):
            raise ValueError("Git Goal path is not canonical")

    def _before_success(self) -> None:
        """The native override independently revalidates Protocol admission."""

    def _primary_identity_ambiguous(self, head: str, tag: str, path: str) -> bool:
        """Preserve compatibility behavior; native overrides this obligation."""

        del head, tag, path
        return False

    def _goal_tree_paths(self, head: str) -> tuple[str, ...]:
        return tuple(
            self._git_text("ls-tree", "-r", "--name-only", head, "--", "docs/goals").splitlines()
        )

    def _regular_goal_blob(self, head: str, path: str) -> str:
        """A committed symlink blob is never a native Goal source."""

        entries = self._git_bytes("ls-tree", "-z", head, "--", path).split(b"\0")
        if len(entries) != 2 or entries[1] != b"":
            raise ValueError("committed_goal_regular_file_required")
        try:
            metadata, listed_path = entries[0].split(b"\t", 1)
            mode, kind, oid = metadata.decode("ascii").split(" ")
            decoded_path = listed_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as error:
            raise ValueError("committed_goal_regular_file_required") from error
        if (
            decoded_path != path
            or mode not in {"100644", "100755"}
            or kind != "blob"
            or len(oid) not in {40, 64}
            or any(character not in "0123456789abcdef" for character in oid)
        ):
            raise ValueError("committed_goal_regular_file_required")
        return oid

    def _is_unique_goal_source(self, head: str, tag: str, path: str) -> bool:
        """A path hint cannot substitute for a unique committed Goal identity."""

        matches: list[str] = []
        for candidate in self._goal_tree_paths(head):
            if not self._candidate_goal_path(candidate):
                continue
            try:
                _ = self._regular_goal_blob(head, candidate)
                _, document = extract_goal_phase_native_document(
                    self._git_bytes("show", f"{head}:{candidate}")
                )
            except (ValueError, TypeError, UnicodeError):
                continue
            if document.goal_tag == tag:
                matches.append(candidate)
        return matches == [path]

    def _candidate_goal_path(self, path: str) -> bool:
        return path.startswith("docs/goals/20") and path.endswith(".md")

    def _refused(
        self,
        request: GoalPhaseObserveEligibilityRequestV1,
        head: str,
        goal_sha: str,
        reason: str,
    ) -> dict[str, object]:
        if self._git_text("rev-parse", "--verify", "HEAD^{commit}") != head:
            reason = "repository_head_advanced"
        result: dict[str, object] = {
            "schema_id": "aware.goal.phase-operation-result.v1",
            "operation_kind": "observe_eligibility",
            "status": "refused",
            "authority_profile": "phase_native_operational_v1",
            "effect_profile": "read_only_non_authorizing",
            "event_effect": "none",
            "dispatch_effect": "none",
            "source_locator_ref": request.source_locator_ref,
            "coordinate": {
                "goal_tag": request.goal_tag,
                "lane_key": request.lane_key,
                "phase_key": request.phase_key,
            },
            "source_revision_ref": head,
            "goal_sha256": goal_sha,
            "eligibility": "refused",
            "reasons": [reason],
        }
        result["decision_ref"] = issue_goal_phase_eligibility_decision_ref(result)
        return result

    def _git_bytes(self, *args: str) -> bytes:
        result = subprocess.run(
            ("git", *args), cwd=self._root, capture_output=True, check=False
        )
        if result.returncode != 0:
            raise ValueError("committed Goal source is unavailable")
        return result.stdout

    def _git_text(self, *args: str) -> str:
        return self._git_bytes(*args).decode("utf-8").strip()


class NativeGitGoalPhaseOperationProvider(_GitGoalPhaseOperationReader):
    """Native entrance: only Protocol-issued retained admission selects scope."""

    def __init__(
        self,
        resolver_capability: object,
        *,
        prerequisite_goal_paths: Mapping[str, str] | None = None,
    ) -> None:
        resolver = _require_native_resolver(resolver_capability)
        super().__init__(
            resolver.repository_root,
            prerequisite_goal_paths=prerequisite_goal_paths,
        )
        self._projector: GitCommittedGoalCompatibilityDirectionProjector = (
            GitCommittedGoalCompatibilityDirectionProjector(
                self._root,
                admitted_issue_location=_NativeAdmittedIssueLocation(resolver),
            )
        )
        self._resolver_capability: object = resolver_capability

    def discover_eligibility_request(
        self, *, goal_path: str, lane_key: str, phase_key: str
    ) -> GoalPhaseObserveEligibilityRequestV1:
        """Derive request identities from one admitted, committed Goal epoch.

        Discovery does not evaluate eligibility or grant a Goal operation effect.
        The later observation independently rereads source and refuses stale
        identities; this request is not a currentness or authorization receipt.
        """

        location = self._resolver().resolve_goal_path(goal_path)
        goal_tag = f"goal/{location.location_date}/{location.location_slug}"
        coordinate = GoalPhaseCoordinate(goal_tag, lane_key, phase_key)
        head = self._git_text("rev-parse", "--verify", "HEAD^{commit}")
        self._validate_goal_path(goal_path, expected_goal_tag=goal_tag)
        blob = self._regular_goal_blob(head, goal_path)
        source = self._git_bytes("show", f"{head}:{goal_path}")
        goal_sha = "sha256:" + hashlib.sha256(source).hexdigest()
        try:
            document, authority = self._projector.project_committed(
                revision_ref=head,
                goal_path=goal_path,
                expected_goal_sha256=goal_sha,
                expected_goal_blob_oid=blob,
            )
        except GoalNativeScopeSourceError as error:
            raise ValueError(error.code) from error
        if document.goal_tag != goal_tag:
            raise ValueError("native_goal_location_identity_mismatch")
        if not self._is_unique_goal_source(head, goal_tag, goal_path):
            raise ValueError("goal_source_ambiguous")
        if not any(item.lane_key == lane_key for item in authority.lane_authorities):
            raise ValueError("lane_authority_absent")
        definitions = tuple(
            item for item in document.definitions if item.coordinate == coordinate
        )
        if len(definitions) != 1:
            raise ValueError("phase_definition_absent_or_ambiguous")
        request = GoalPhaseObserveEligibilityRequestV1(
            source_locator_ref="repository-path:" + goal_path,
            goal_tag=goal_tag,
            lane_key=lane_key,
            phase_key=phase_key,
            expected_goal_sha256=goal_sha,
            expected_native_document_ref=document.document_ref,
            expected_gate_digest=definitions[0].gate.gate_digest,
        )
        self._before_success()
        if self._git_text("rev-parse", "--verify", "HEAD^{commit}") != head:
            raise ValueError("repository_head_advanced")
        return request

    def _resolver(self) -> _NativeGoalResolver:
        return _require_native_resolver(self._resolver_capability)

    @override
    def _validate_goal_path(self, path: str, *, expected_goal_tag: str) -> None:
        location = self._resolver().resolve_goal_path(path)
        if expected_goal_tag != (
            f"goal/{location.location_date}/{location.location_slug}"
        ):
            raise ValueError("native_goal_location_identity_mismatch")

    @override
    def _goal_tree_paths(self, head: str) -> tuple[str, ...]:
        root = self._resolver().goal_root
        return tuple(
            self._git_text("ls-tree", "-r", "--name-only", head, "--", root).splitlines()
        )

    @override
    def _candidate_goal_path(self, path: str) -> bool:
        return self._resolver().match_goal_path(path) is not None

    @override
    def _before_success(self) -> None:
        self._resolver().revalidate()

    @override
    def _primary_identity_ambiguous(self, head: str, tag: str, path: str) -> bool:
        return not self._is_unique_goal_source(head, tag, path)
