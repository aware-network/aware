"""Git preparation, never an Issue evaluator or publication implementation."""
import os
from pathlib import Path
import subprocess

from aware_repository_sdk import RepositoryPrepareRequest, RepositoryPrepareResult


def git(root: Path, *arguments: str):
    # Ambient GIT_DIR/GIT_WORK_TREE must not substitute a different target.
    environment = {k: v for k, v in os.environ.items() if k in {"PATH", "HOME", "LANG", "LC_ALL"}}
    return subprocess.run(["git", "-C", str(root), *arguments], env=environment,
                          capture_output=True, text=True, check=False)


def check_path(path: Path):
    for candidate in [*reversed(path.parents), path]:
        if candidate.is_symlink():
            raise ValueError("repository_symlink_path_refused")
        if candidate.exists() and not candidate.is_dir():
            raise ValueError("repository_directory_required")


class FilesystemRepositoryPrepareProvider:
    def prepare_repository(self, request: RepositoryPrepareRequest) -> RepositoryPrepareResult:
        if type(request) is not RepositoryPrepareRequest:
            raise TypeError("RepositoryPrepareRequest_required")
        root = Path(request.repository_root)

        def result(outcome, *diagnostics, head=None):
            return RepositoryPrepareResult(outcome, str(root), head, tuple(diagnostics))

        try:
            check_path(root)
            if not root.parent.is_dir():
                return result("refused", "repository_parent_directory_required")
            probe = root if root.is_dir() else root.parent
            discovery = git(probe, "rev-parse", "--show-toplevel")
            if discovery.returncode == 0:
                actual = Path(discovery.stdout.strip()).resolve(strict=True)
                if actual != root:
                    return result("refused", "select_exact_git_repository_root", "nested_repository_creation_refused")
                if (root / ".git").is_symlink():
                    return result("refused", "repository_git_metadata_symlink_refused")
                head = git(root, "rev-parse", "--verify", "HEAD^{commit}")
                return result("existing", head=head.stdout.strip() if head.returncode == 0 else None)
            if git(probe, "rev-parse", "--is-bare-repository").returncode == 0:
                return result("refused", "bare_repository_not_supported")
            if not request.create_if_missing:
                return result("refused", "git_repository_required", "use_init_create_repository_for_an_empty_target")
            if root.exists() and any(root.iterdir()):
                return result("refused", "repository_creation_requires_empty_target")
            if request.dry_run:
                return result("planned", "empty_repository_preparation_only_no_commit")
            check_path(root)
            root.mkdir(exist_ok=True)
            if any(root.iterdir()):
                return result("refused", "repository_target_changed_during_preparation")
            created = git(root, "-c", "init.templateDir=", "init", "--template=", "--initial-branch=main", ".")
            if created.returncode:
                return result("refused", "repository_git_initialization_failed", "inspect_retained_target_before_retry")
            observed = git(root, "rev-parse", "--show-toplevel")
            if observed.returncode or Path(observed.stdout.strip()).resolve() != root:
                return result("refused", "repository_creation_identity_unproven", "inspect_retained_target_before_retry")
            return result("created", "unborn_head_first_publication_requires_issue")
        except (OSError, ValueError) as error:
            return result("refused", str(error) if isinstance(error, ValueError) else "repository_source_unavailable:" + type(error).__name__)
