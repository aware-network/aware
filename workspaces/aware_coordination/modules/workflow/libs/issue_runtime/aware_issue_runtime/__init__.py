from .contracts import (
    ISSUE_PROJECTION_SCHEMA_VERSION,
    IssueAcceptanceProjection,
    IssueActivityProjection,
    IssueAdditionalSectionProjection,
    IssueEvidenceProjection,
    IssueReadProjection,
    IssueSourceDocument,
    IssueSourceHeader,
    IssueSourceSection,
    IssueTimeAuthority,
)
from .development import (
    ISSUE_DEVELOPMENT_READ_PROJECTION_V2_SCHEMA,
    build_issue_development_read_payload_v2,
    issue_development_read_payload_v2_from_runtime,
    normalize_issue_activity_kind_payload_v1,
    normalize_issue_lifecycle_payload_v1,
)
from .first_person_activity import (
    FIRST_PERSON_ISSUE_ACTIVITY_SCHEMA_V1,
    build_first_person_issue_activity_payload_v1,
)
from .parser import parse_issue_projection, parse_issue_source
from .pulse import (
    REPOSITORY_PULSE_ACTIVITY_SCHEMA_V1,
    REPOSITORY_PULSE_SCHEMA_V1,
    build_repository_pulse_payload_v1,
)
from .source_import import (
    IssueSourceImportAdmission,
    IssueSourceImportProposal,
    admit_issue_source_import,
    propose_issue_source_import,
)

__all__ = [
    "FIRST_PERSON_ISSUE_ACTIVITY_SCHEMA_V1",
    "ISSUE_DEVELOPMENT_READ_PROJECTION_V2_SCHEMA",
    "ISSUE_PROJECTION_SCHEMA_VERSION",
    "REPOSITORY_PULSE_ACTIVITY_SCHEMA_V1",
    "REPOSITORY_PULSE_SCHEMA_V1",
    "IssueAcceptanceProjection",
    "IssueActivityProjection",
    "IssueAdditionalSectionProjection",
    "IssueEvidenceProjection",
    "IssueReadProjection",
    "IssueSourceDocument",
    "IssueSourceHeader",
    "IssueSourceImportAdmission",
    "IssueSourceImportProposal",
    "IssueSourceSection",
    "IssueTimeAuthority",
    "admit_issue_source_import",
    "build_first_person_issue_activity_payload_v1",
    "build_issue_development_read_payload_v2",
    "build_repository_pulse_payload_v1",
    "issue_development_read_payload_v2_from_runtime",
    "normalize_issue_activity_kind_payload_v1",
    "normalize_issue_lifecycle_payload_v1",
    "parse_issue_projection",
    "parse_issue_source",
    "propose_issue_source_import",
]


def __getattr__(name: str):
    raise AttributeError(f"module 'aware_issue_runtime' has no attribute {name!r}")
