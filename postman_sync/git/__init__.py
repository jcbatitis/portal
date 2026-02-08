"""Git integration modules."""

from .hook_installer import GitHookInstaller, GitHookError
from .stage_manager import GitStageManager, GitStageError

__all__ = [
    "GitHookInstaller",
    "GitHookError",
    "GitStageManager",
    "GitStageError",
]
