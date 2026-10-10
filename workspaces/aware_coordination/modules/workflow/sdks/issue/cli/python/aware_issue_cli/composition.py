"""Explicit consumer wiring, never a foreign SDK dispatcher in an FS adapter."""

from pathlib import Path


def create_repository_client(*, provider, repository_root):
    # Lazy: read/lifecycle commands do not import publication or Service rails.
    from aware_issue_fs_adapter.repository_publication import (
        FilesystemIssueRepositorySourcePort,
    )
    from aware_issue_operational_runtime.repository_publication import (
        IssueRepositoryPublicationRuntime,
    )
    from aware_issue_sdk.repository_publication import IssueRepositoryPublicationClient
    from aware_workspace_sdk.repository_publication.authority import (
        WorkspaceRepositoryPublicationClient,
    )

    root = Path(repository_root)
    # Do not resolve symlinks or guess another repository on the consumer's behalf.
    workspace = WorkspaceRepositoryPublicationClient.filesystem(repository_root=root)
    return IssueRepositoryPublicationClient(
        IssueRepositoryPublicationRuntime(
            source_port=FilesystemIssueRepositorySourcePort(provider),
            workspace_client=workspace,
        )
    )
