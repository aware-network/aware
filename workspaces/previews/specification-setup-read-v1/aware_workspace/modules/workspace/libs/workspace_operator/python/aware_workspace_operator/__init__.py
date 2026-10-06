from importlib import import_module
_EXPORT_MODULES = {'run_workspace_commit': '.commit', 'verify_repository_commit_receipt': '.commit', 'WorkspaceCommitIssueMetadata': '.models', 'WorkspaceCommitOptions': '.models', 'WorkspaceCommitOutcome': '.models'}
__all__ = sorted(_EXPORT_MODULES)
def __getattr__(name):
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(name)
    value = getattr(import_module(module_name, package=__name__), name)
    globals()[name] = value
    return value
