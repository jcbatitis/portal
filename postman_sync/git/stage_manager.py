"""Git staging operations for postman-sync."""

from pathlib import Path
import subprocess

from ..utils.logger import get_logger

logger = get_logger("git.stage")


class GitStageError(Exception):
    """Git staging operation failed."""
    pass


class GitStageManager:
    """Manages Git staging operations."""

    def __init__(self, repo_root: Path):
        """
        Initialize stage manager.

        Args:
            repo_root: Root of Git repository
        """
        self.repo_root = repo_root

    def stage_files(self, file_paths: list[Path]) -> None:
        """
        Stage files for commit.

        Args:
            file_paths: List of file paths to stage

        Raises:
            GitStageError: If staging fails
        """
        if not file_paths:
            logger.debug("No files to stage")
            return

        for path in file_paths:
            try:
                # Convert to relative path if absolute
                if path.is_absolute():
                    try:
                        relative_path = path.relative_to(self.repo_root)
                    except ValueError:
                        # Path is outside repo
                        relative_path = path
                else:
                    relative_path = path

                subprocess.run(
                    ["git", "add", str(relative_path)],
                    cwd=self.repo_root,
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.debug(f"Staged: {relative_path}")

            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.strip() if e.stderr else str(e)
                raise GitStageError(f"Failed to stage {path}: {error_msg}") from e

        logger.info(f"✅ Staged {len(file_paths)} file(s)")

    def is_file_staged(self, file_path: Path) -> bool:
        """
        Check if file is staged for commit.

        Args:
            file_path: Path to check

        Returns:
            True if file is staged
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
                text=True
            )

            staged_files = result.stdout.strip().split('\n')
            file_str = str(file_path)

            return any(file_str in staged_file for staged_file in staged_files)

        except subprocess.CalledProcessError:
            return False

    def get_staged_route_files(self) -> list[Path]:
        """
        Get list of staged TypeScript route files.

        Returns:
            List of staged route file paths
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
                text=True
            )

            staged_files = result.stdout.strip().split('\n')

            # Filter for route files
            route_files = [
                self.repo_root / f
                for f in staged_files
                if 'src/routes/' in f and f.endswith('.ts')
            ]

            return route_files

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get staged files: {e}")
            return []
