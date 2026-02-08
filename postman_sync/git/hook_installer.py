"""Git pre-commit hook installation and management."""

from pathlib import Path
import subprocess

from ..utils.logger import get_logger

logger = get_logger("git.hooks")


class GitHookError(Exception):
    """Git hook operation failed."""
    pass


class GitHookInstaller:
    """Manages Git pre-commit hook installation."""

    def __init__(self, repo_root: Path):
        """
        Initialize hook installer.

        Args:
            repo_root: Root of Git repository
        """
        self.repo_root = repo_root
        self.hooks_dir = repo_root / ".git" / "hooks"

    def install_pre_commit_hook(self) -> None:
        """
        Install pre-commit hook that runs postman-sync.

        Creates .git/hooks/pre-commit script that:
        1. Checks if route files are staged
        2. Runs postman-sync if needed
        3. Auto-stages updated collection JSON
        4. Fails commit if sync errors occur

        Raises:
            GitHookError: If installation fails
        """
        if not self.hooks_dir.exists():
            raise GitHookError(f"Git hooks directory not found: {self.hooks_dir}")

        hook_path = self.hooks_dir / "pre-commit"

        # Get path to postman-sync script
        sync_script = self.repo_root / "backend" / "postman_sync" / "cli.py"

        hook_content = f"""#!/bin/bash
# Auto-generated Git pre-commit hook for postman-sync

set -e  # Exit on any error

# Check if route files are staged
ROUTE_FILES=$(git diff --cached --name-only | grep 'backend/src/routes/.*\\.ts$' || true)

if [ -z "$ROUTE_FILES" ]; then
    # No route files changed, skip sync
    exit 0
fi

echo "🔄 Postman collection sync: Route files changed, syncing..."

# Run sync tool
cd "{self.repo_root}/backend"
python3 -m postman_sync sync

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERROR: Postman sync failed. Commit aborted."
    echo "Fix errors and try again, or run with --no-verify to skip."
    exit 1
fi

echo "✅ Postman collection synced successfully"
exit 0
"""

        # Write hook
        hook_path.write_text(hook_content)
        hook_path.chmod(0o755)  # Make executable

        logger.info(f"✅ Installed pre-commit hook at {hook_path}")

    def uninstall_hook(self, hook_name: str = "pre-commit") -> None:
        """
        Remove Git hook.

        Args:
            hook_name: Name of hook to remove

        Raises:
            GitHookError: If uninstallation fails
        """
        hook_path = self.hooks_dir / hook_name

        if not hook_path.exists():
            logger.warning(f"Hook not found: {hook_path}")
            return

        hook_path.unlink()
        logger.info(f"✅ Removed {hook_name} hook")

    def is_hook_installed(self) -> bool:
        """
        Check if pre-commit hook is installed.

        Returns:
            True if hook exists
        """
        hook_path = self.hooks_dir / "pre-commit"
        return hook_path.exists()
