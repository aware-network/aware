"""Original Protocol binding policy observed without selection/write issuance."""

from __future__ import annotations

import os
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from aware_protocol_sdk.specification_target_fit import (
    PROTOCOL_SPECIFICATION_TARGET_FIT_DISTRIBUTION,
    PROTOCOL_SPECIFICATION_TARGET_FIT_PROVIDER_REF,
    ProtocolSpecificationTargetFitError,
    ProtocolSpecificationTargetFitErrorEvidence,
    ProtocolSpecificationTargetFitRequest,
    ProtocolSpecificationTargetFitResult,
    protocol_specification_target_fit_value_from_payload,
    protocol_specification_target_fit_value_to_payload,
)
from aware_protocol_sdk.specification_target_fit import (
    ProtocolSpecificationTargetFitCleanup as Cleanup,
)
from aware_protocol_sdk.specification_target_fit import (
    ProtocolSpecificationTargetFitEffect as Effect,
)
from aware_protocol_sdk.specification_target_fit import (
    ProtocolSpecificationTargetFitEvidenceGrade as Grade,
)
from aware_protocol_sdk.specification_target_fit import (
    ProtocolSpecificationTargetFitOutcome as Fit,
)

from . import specification_selection as owner
from .manifest import admit_protocol_manifest_bytes


def _detached[
    T: (ProtocolSpecificationTargetFitRequest, ProtocolSpecificationTargetFitResult)
](value: T) -> T:
    return protocol_specification_target_fit_value_from_payload(
        type(value), protocol_specification_target_fit_value_to_payload(value)
    )


class FilesystemProtocolSpecificationTargetFitProvider:
    def observe_specification_target_fit(
        self, request: ProtocolSpecificationTargetFitRequest
    ) -> ProtocolSpecificationTargetFitResult:
        original = None
        descriptor = None
        cleanup = Cleanup.NOT_ACQUIRED
        effect = Effect.NONE
        observed_digest: str | None = None
        configured_root: str | None = None
        path_template: str | None = None
        expected_shape: str | None = None
        observed_fit: Fit | None = None
        failure: BaseException | None = None
        code = "specification_target_fit_source_unavailable"
        diagnostics: tuple[str, ...] = ()
        result_args: (
            tuple[
                ProtocolSpecificationTargetFitRequest,
                str,
                str,
                str,
                str,
                str,
                str,
                str,
                Fit,
                str,
            ]
            | None
        ) = None
        key: str | None = None
        try:
            original = _detached(request)
            if type(original) is not ProtocolSpecificationTargetFitRequest:
                raise owner.SpecificationSelectionError(
                    "specification_target_fit_request_invalid"
                )
            paths = (original.supplied_spec_manifest_locator,)
            owner._validate_specification_locators(paths)
            root = Path(original.repository_root).resolve(strict=True)
            source = Path(original.protocol_manifest_locator)
            source = (source if source.is_absolute() else root / source).absolute()
            try:
                relative = source.relative_to(root).as_posix()
            except ValueError as error:
                raise owner.SpecificationSelectionError(
                    "specification_selection_manifest_outside_repository"
                ) from error
            if (
                not owner._canonical(relative)
                or relative.split("/")[-1] != "aware.protocol.toml"
            ):
                raise owner.SpecificationSelectionError(
                    "specification_selection_manifest_unresolvable"
                )
            descriptor = os.open(
                root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
            )
            cleanup = Cleanup.UNKNOWN
            identity = owner._identity(descriptor)
            namespace = owner._namespace()
            body, manifest_identity, parents = owner._manifest_source(
                descriptor, relative
            )
            digest = "sha256:" + sha256(body).hexdigest()
            observed_digest = digest
            if digest != original.expected_manifest_sha256:
                raise owner.SpecificationSelectionError(
                    "specification_selection_manifest_changed"
                )
            admission = admit_protocol_manifest_bytes(source=body, repository_root=root)
            profile = admission.filesystem_profile
            if profile is None:
                raise owner.SpecificationSelectionError(
                    "specification_target_fit_manifest_refused",
                    diagnostics=tuple(
                        str(item)[:1024] for item in admission.diagnostics[:15]
                    ),
                )
            # Empty target list asks the same owner for its validated binding,
            # including on mismatch. It does not relax the prior locator check.
            binding, _ = owner._specification_binding_layout(profile, ())
            shape = binding.root + "/" + binding.path_template
            configured_root = binding.root
            path_template = binding.path_template
            expected_shape = shape
            fit = Fit.MATCH
            key = None
            reason = "specification_selection_target_matches_binding"
            try:
                _, roots = owner._specification_binding_layout(profile, paths)
                key = roots[0].rsplit("/", 1)[-1]
            except owner.SpecificationSelectionError as error:
                if error.code != "specification_selection_target_outside_binding":
                    raise
                fit = Fit.MISMATCH
                reason = error.code
            observed_fit = fit
            try:
                distribution_version = version(
                    PROTOCOL_SPECIFICATION_TARGET_FIT_DISTRIBUTION
                )
            except PackageNotFoundError:
                distribution_version = "source"
            current = os.open(
                root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
            )
            try:
                if owner._identity(current) != identity:
                    raise owner.SpecificationSelectionError(
                        "specification_selection_repository_changed"
                    )
            finally:
                os.close(current)
            # Retain original bytes/physical identities and guard at return-time.
            again, again_identity, again_parents = owner._manifest_source(
                descriptor, relative
            )
            if (
                again != body
                or again_identity != manifest_identity
                or again_parents != parents
                or owner._identity(descriptor) != identity
                or owner._namespace() != namespace
            ):
                raise owner.SpecificationSelectionError(
                    "specification_selection_manifest_changed"
                )
            # Retain inputs; construct a result only after confirmed cleanup.
            result_args = (
                original,
                PROTOCOL_SPECIFICATION_TARGET_FIT_PROVIDER_REF,
                PROTOCOL_SPECIFICATION_TARGET_FIT_DISTRIBUTION,
                distribution_version,
                digest,
                binding.root,
                binding.path_template,
                shape,
                fit,
                reason,
            )
        except BaseException as error:  # noqa: BLE001 -- retain original observation/cleanup on interruption
            failure = error
            if type(error) is owner.SpecificationSelectionError:
                code, diagnostics = error.code, error.diagnostics
                if code == "specification_selection_manifest_cleanup_unverified":
                    effect = Effect.UNKNOWN
            else:
                diagnostics = (f"observation_failure:{type(error).__name__}",)
                # Original nested read cleanup may have been interrupted.
                if descriptor is not None:
                    effect = Effect.UNKNOWN
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except BaseException as error:  # noqa: BLE001 -- failed closes remain unknown and are never retried
                    cleanup, effect = Cleanup.UNKNOWN, Effect.UNKNOWN
                    diagnostics = (
                        *diagnostics[:15],
                        f"target_fit_cleanup_failed:{type(error).__name__}",
                    )
                    if failure is None:
                        failure = error
                        code = "specification_target_fit_cleanup_unverified"
                else:
                    cleanup = (
                        Cleanup.CLOSED if effect is Effect.NONE else Cleanup.UNKNOWN
                    )
        if failure is None:
            try:
                assert result_args is not None
                return _detached(
                    ProtocolSpecificationTargetFitResult(
                        *result_args,
                        diagnostics=(result_args[-1],),
                        matched_spec_key=key,
                    )
                )
            except BaseException as error:  # noqa: BLE001 -- late value failures must retain observed evidence
                failure = error
                code = "specification_target_fit_result_unverified"
                diagnostics = (f"result_failure:{type(error).__name__}",)
        raise ProtocolSpecificationTargetFitError(
            ProtocolSpecificationTargetFitErrorEvidence(
                code=code,
                message="Target-fit observation refused; no write authority was issued.",
                request=original,
                provider_invoked=True,
                cleanup=cleanup,
                effect=effect,
                diagnostics=diagnostics,
                evidence_grade=Grade.PROVIDER_OBSERVATION,
                observed_source_sha256=observed_digest,
                configured_root=configured_root,
                path_template=path_template,
                expected_shape=expected_shape,
                observed_fit=observed_fit,
            )
        ) from failure
