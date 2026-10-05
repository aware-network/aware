# Neutral filesystem repository preparation

Implements `repository_sdk.prepare_repository`. New targets must be empty with
an existing parent. Symlink paths, nested repository creation, bare repositories
and nonempty non-Git directories are refused. Existing exact non-bare Git roots
are reused without reinitialization; unborn HEAD is supported.

Preparation sets a new branch to `main`, suppresses imported Git templates,
and performs no commit, staging, author configuration, remote setup or push.
Git is the local provider, not another semantic authority. Normal Issue-scoped
publication uses the existing neutral owner, unchanged.

These checks are not hostile-process filesystem isolation. Preparation and
scaffold writes are a non-atomic composition; failures retain inspectable state.
