"""Command-line interface for postman-sync."""

import sys
from pathlib import Path

from .config import Config, ConfigError
from .sync.engine import SyncEngine, SyncError
from .git.hook_installer import GitHookInstaller, GitHookError
from .utils.logger import setup_logger, get_logger


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    # Handle commands
    if command == "sync":
        sys.exit(cmd_sync())
    elif command == "install-hook":
        sys.exit(cmd_install_hook())
    elif command == "uninstall-hook":
        sys.exit(cmd_uninstall_hook())
    elif command == "validate":
        sys.exit(cmd_validate())
    elif command in ("--help", "-h", "help"):
        print_usage()
        sys.exit(0)
    else:
        print(f"❌ Unknown command: {command}")
        print()
        print_usage()
        sys.exit(1)


def print_usage():
    """Print CLI usage help."""
    print("""
postman-sync - Sync Fastify routes to Postman collections

USAGE:
    python -m postman_sync <command>

COMMANDS:
    sync              Sync routes to Postman collection
    install-hook      Install Git pre-commit hook
    uninstall-hook    Remove Git pre-commit hook
    validate          Validate configuration and setup
    help              Show this help message

EXAMPLES:
    # Sync routes (typically called by git hook)
    python -m postman_sync sync

    # Install git hook for automatic syncing
    python -m postman_sync install-hook

    # Validate setup before first use
    python -m postman_sync validate

CONFIGURATION:
    Set environment variables in .env file:
    - POSTMAN_API_KEY
    - POSTMAN_COLLECTION_ID
    - POSTMAN_ROUTES_DIR (default: src/routes)
    - POSTMAN_COLLECTION_FILE (default: postman/tracker-backend-api.postman_collection.json)
    - POSTMAN_DEPRECATION_DAYS (default: 30)
    - POSTMAN_AUTO_STAGE (default: true)
    - POSTMAN_FAIL_ON_ERROR (default: true)
    - POSTMAN_LOG_LEVEL (default: INFO)

See .env.example for full configuration reference.
""")


def cmd_sync() -> int:
    """
    Execute sync command.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        # Load config
        config = Config.from_env()

        # Setup logger
        logger = setup_logger(level=config.log_level)

        # Run sync
        engine = SyncEngine(config)
        result = engine.run_sync()

        if result.has_errors:
            logger.error("❌ Sync completed with errors")
            for error in result.errors:
                logger.error(f"  - {error}")
            return 1

        return 0

    except ConfigError as e:
        print(f"❌ Configuration error: {e}", file=sys.stderr)
        print("Check your .env file and ensure all required variables are set.", file=sys.stderr)
        return 1

    except SyncError as e:
        print(f"❌ Sync failed: {e}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\n⚠️  Sync cancelled by user", file=sys.stderr)
        return 130

    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_install_hook() -> int:
    """
    Install Git pre-commit hook.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        config = Config.from_env()
        logger = setup_logger(level=config.log_level)

        installer = GitHookInstaller(config.repo_root)

        if installer.is_hook_installed():
            logger.warning("⚠️  Pre-commit hook already installed")
            response = input("Overwrite existing hook? [y/N]: ")
            if response.lower() != 'y':
                logger.info("Cancelled")
                return 0

        installer.install_pre_commit_hook()
        print()
        print("✅ Git pre-commit hook installed successfully!")
        print()
        print("The hook will automatically run when you commit changes to route files.")
        print("To skip the hook for a specific commit, use: git commit --no-verify")

        return 0

    except (ConfigError, GitHookError) as e:
        print(f"❌ Failed to install hook: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


def cmd_uninstall_hook() -> int:
    """
    Uninstall Git pre-commit hook.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        config = Config.from_env()
        logger = setup_logger(level=config.log_level)

        installer = GitHookInstaller(config.repo_root)

        if not installer.is_hook_installed():
            logger.warning("⚠️  Pre-commit hook not installed")
            return 0

        installer.uninstall_hook()
        print("✅ Git pre-commit hook removed")

        return 0

    except (ConfigError, GitHookError) as e:
        print(f"❌ Failed to uninstall hook: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


def cmd_validate() -> int:
    """
    Validate configuration and setup.

    Returns:
        Exit code (0 = valid, 1 = invalid)
    """
    try:
        config = Config.from_env()
        logger = setup_logger(level=config.log_level)

        print("🔍 Validating postman-sync setup...")
        print()

        # Validate configuration
        print("✅ Configuration loaded successfully")
        print(f"   Routes directory: {config.routes_directory}")
        print(f"   Collection file: {config.collection_file}")
        print(f"   Collection ID: {config.postman_collection_id}")
        print()

        # Validate sync engine
        engine = SyncEngine(config)
        errors = engine.validate_setup()

        if errors:
            print("❌ Validation failed:")
            for error in errors:
                print(f"   - {error}")
            print()
            return 1

        print("✅ All checks passed!")
        print()
        print("Ready to sync. Run: python -m postman_sync sync")

        return 0

    except ConfigError as e:
        print(f"❌ Configuration error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    main()
