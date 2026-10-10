import threading
from dataclasses import replace
from types import SimpleNamespace
from weakref import WeakKeyDictionary

import pytest
from aware_code_semantic_contract_runtime import (
    CodeSemanticCandidate,
    CodeSemanticCandidateListing,
    ContentDigest,
    SemanticConfigurationCoordinate,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    SemanticInputPackageIdentity,
    SemanticInputProducerDeclaration,
    SemanticInputProducerHost,
    SemanticInputProductionExpectation,
    SemanticInputSourceContract,
    SemanticInputSourceCoordinate,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
    execute_registered_semantic_input,
    register_semantic_input_producer,
)
from aware_code_semantic_contract_runtime.runtime import SemanticBody
from aware_workspace_runtime.observed_membership import (
    WorkspaceObservedPackageMembership,
)
from aware_workspace_runtime.source_admission import (
    WorkspaceOwnerDefinedSourceAdmission,
    WorkspaceOwnerDefinedSourceAdmissionRuntime,
)


def test_source_authority_types_require_owner_assembly():
    with pytest.raises(TypeError, match="Workspace issues"):
        WorkspaceOwnerDefinedSourceAdmission()
    with pytest.raises(TypeError, match="fixed assembly"):
        WorkspaceOwnerDefinedSourceAdmissionRuntime()


def _semantic_input_fixture(monkeypatch):
    body = b"same retained bytes"
    digest = ContentDigest.of_bytes(body)
    contract = SemanticContractRef("example.source.v1", "1", digest)
    coordinates = tuple(
        SemanticInputSourceCoordinate(
            path,
            SemanticValueCoordinate(
                role,
                contract,
                f"cas://{role}",
                digest,
                len(body),
            ),
        )
        for path, role in (
            ("aware.owner.toml", "manifest"),
            ("bindings/source.aware", "source"),
        )
    )
    listing = CodeSemanticCandidateListing(
        ContentDigest.of_bytes(b"source identity"),
        tuple(
            CodeSemanticCandidate(source.relative_path, digest)
            for source in coordinates
        ),
    )
    membership = object.__new__(WorkspaceObservedPackageMembership)
    admission = object.__new__(WorkspaceOwnerDefinedSourceAdmission)
    bodies = {source.relative_path: body for source in coordinates}

    class MembershipRuntime:
        def evidence(self, original):
            assert original is membership
            return SimpleNamespace(
                manifest_relative_path="aware.owner.toml",
                candidate_listing=listing,
            )

        def read(self, original, *, relative_path):
            assert original is membership
            return bodies[relative_path]

    runtime = object.__new__(WorkspaceOwnerDefinedSourceAdmissionRuntime)
    runtime._membership_runtime = MembershipRuntime()
    runtime._records = WeakKeyDictionary()
    runtime._lock = threading.RLock()
    runtime._closed = False
    package = SemanticPackageCoordinate(
        "package:example@1.0.0",
        "ontology",
        ContentDigest.of_bytes(b"aware.owner.toml"),
    )
    record = SimpleNamespace(
        membership=membership,
        inspection=SimpleNamespace(
            package=package,
            package_authority=SimpleNamespace(
                declared_source_paths=("bindings/source.aware",),
                semantic_package=SimpleNamespace(name="example"),
            )
        ),
    )
    runtime._records[admission] = record
    validations = []
    monkeypatch.setattr(
        WorkspaceOwnerDefinedSourceAdmissionRuntime,
        "_validate_record",
        lambda self, original: validations.append(original),
    )
    operation = object()
    expected = SemanticInputProductionExpectation.create(
        use_ref="use-1",
        operation_ref="operation-1",
        stage="definition_request",
        package_identity=SemanticInputPackageIdentity(package, "example"),
        operation_identity=operation,
        source_identity=admission,
        source_coordinates=coordinates,
    )
    return runtime, admission, expected, bodies, validations


def test_semantic_input_reader_preserves_path_identity_for_equal_bodies(monkeypatch):
    runtime, admission, expected, _, validations = _semantic_input_fixture(monkeypatch)

    assert runtime.validate_semantic_input_source(admission, expected=expected) is None
    sources = runtime.read_semantic_input_sources(admission, expected=expected)

    assert tuple(source.source for source in sources) == expected.source_coordinates
    assert tuple(source.canonical_body for source in sources) == (
        b"same retained bytes",
        b"same retained bytes",
    )
    assert validations == [runtime._records[admission]] * 4


def test_semantic_input_reader_rejects_identity_path_and_body_substitution(monkeypatch):
    runtime, admission, expected, bodies, _ = _semantic_input_fixture(monkeypatch)
    foreign = object.__new__(WorkspaceOwnerDefinedSourceAdmission)

    with pytest.raises(RuntimeError, match="foreign_or_expired"):
        runtime.validate_semantic_input_source(foreign, expected=expected)
    with pytest.raises(RuntimeError, match="source_identity_mismatch"):
        runtime.validate_semantic_input_source(
            admission,
            expected=SemanticInputProductionExpectation.create(
                use_ref="use-1",
                operation_ref="operation-1",
                stage="definition_request",
                package_identity=expected.package_identity,
                operation_identity=expected.operation_identity,
                source_identity=foreign,
                source_coordinates=expected.source_coordinates,
            ),
        )

    foreign_package = SemanticPackageCoordinate(
        "package:foreign@1.0.0",
        expected.package_identity.package.package_kind,
        expected.package_identity.package.manifest_digest,
    )
    with pytest.raises(RuntimeError, match="package_coordinate_mismatch"):
        runtime.validate_semantic_input_source(
            admission,
            expected=SemanticInputProductionExpectation.create(
                use_ref="use-package",
                operation_ref="operation-1",
                stage="definition_request",
                package_identity=replace(
                    expected.package_identity, package=foreign_package
                ),
                operation_identity=expected.operation_identity,
                source_identity=admission,
                source_coordinates=expected.source_coordinates,
            ),
        )
    with pytest.raises(RuntimeError, match="package_name_mismatch"):
        runtime.validate_semantic_input_source(
            admission,
            expected=SemanticInputProductionExpectation.create(
                use_ref="use-name",
                operation_ref="operation-1",
                stage="definition_request",
                package_identity=replace(
                    expected.package_identity, package_name="foreign"
                ),
                operation_identity=expected.operation_identity,
                source_identity=admission,
                source_coordinates=expected.source_coordinates,
            ),
        )

    foreign_path = SemanticInputSourceCoordinate(
        "undeclared.aware", expected.source_coordinates[1].coordinate
    )
    with pytest.raises(RuntimeError, match="source_not_admitted"):
        runtime.validate_semantic_input_source(
            admission,
            expected=SemanticInputProductionExpectation.create(
                use_ref="use-2",
                operation_ref="operation-1",
                stage="definition_request",
                package_identity=expected.package_identity,
                operation_identity=expected.operation_identity,
                source_identity=admission,
                source_coordinates=(foreign_path,),
            ),
        )

    bodies["bindings/source.aware"] = b"changed retained bytes"
    with pytest.raises(ValueError, match="source body differs"):
        runtime.read_semantic_input_sources(admission, expected=expected)


def test_semantic_input_reader_rejects_digest_substitution_and_close(monkeypatch):
    runtime, admission, expected, _, _ = _semantic_input_fixture(monkeypatch)
    substituted = SemanticInputSourceCoordinate(
        expected.source_coordinates[0].relative_path,
        SemanticValueCoordinate(
            "manifest",
            expected.source_coordinates[0].coordinate.contract,
            "cas://substituted",
            ContentDigest.of_bytes(b"substituted"),
            len(b"substituted"),
        ),
    )
    with pytest.raises(RuntimeError, match="coordinate_mismatch"):
        runtime.validate_semantic_input_source(
            admission,
            expected=SemanticInputProductionExpectation.create(
                use_ref="use-3",
                operation_ref="operation-1",
                stage="definition_request",
                package_identity=expected.package_identity,
                operation_identity=expected.operation_identity,
                source_identity=admission,
                source_coordinates=(substituted,),
            ),
        )

    runtime.close()
    with pytest.raises(RuntimeError, match="foreign_or_expired"):
        runtime.validate_semantic_input_source(admission, expected=expected)


@pytest.mark.asyncio
async def test_existing_workspace_admission_conforms_to_code_producer_host(monkeypatch):
    runtime, admission, expected, _, _ = _semantic_input_fixture(monkeypatch)
    result_body = b"detached owner meaning"
    result_contract = SemanticContractRef(
        "example.result.v1", "1", ContentDigest.of_bytes(b"result schema")
    )
    declaration = SemanticInputProducerDeclaration(
        "example.owner.definition-request",
        "example.owner.definition-request.v1",
        SemanticImplementationCoordinate(
            "example-owner@1/definition-request",
            ContentDigest.of_bytes(b"implementation"),
        ),
        SemanticConfigurationCoordinate(
            "example.owner.definition-request.config.v1",
            ContentDigest.of_bytes(b"configuration"),
        ),
        tuple(
            SemanticInputSourceContract(source.coordinate.role, source.coordinate.contract)
            for source in expected.source_coordinates
        ),
        "definition_request",
        result_contract,
    )
    received = []

    def produce(value):
        received.append(value)
        return SemanticBody(
            SemanticValueCoordinate(
                "definition_request",
                result_contract,
                "cas://definition-request",
                ContentDigest.of_bytes(result_body),
                len(result_body),
            ),
            result_body,
        )

    host = SemanticInputProducerHost()
    registration = register_semantic_input_producer(
        host,
        declaration=declaration,
        producer=produce,
        validator=runtime,
        validator_entrance=runtime.validate_semantic_input_source,
        reader=runtime,
        reader_entrance=runtime.read_semantic_input_sources,
    )
    result = await execute_registered_semantic_input(
        host,
        registration,
        source_admission=admission,
        expected=expected,
    )

    assert result.canonical_body == result_body
    assert len(received) == 1
    assert not hasattr(received[0], "source_admission")
    assert tuple(source.source for source in received[0].sources) == (
        expected.source_coordinates
    )
