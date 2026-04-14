"""
cli.py
CLI parsing for SnapOut actions.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any


# Command descriptions for help text
COMMAND_INFO = {
    "scan-all": {
        "help": "Scan all Snap packages (active and old)",
        "description": "Display a complete list of all Snap packages installed on the system, showing both active packages and old disabled versions.",
        "epilog": "This is a read-only operation. No changes are made to the system.",
    },
    "scan-active": {
        "help": "Scan only active Snap packages",
        "description": "Display only the currently active Snap packages installed on the system.",
        "epilog": "This is a read-only operation. No changes are made to the system.",
    },
    "scan-old": {
        "help": "Scan only old Snap versions",
        "description": "Display old/disabled Snap versions that are candidates for cleanup. These are previous revisions kept by Snap for rollback purposes.",
        "epilog": "This is a read-only operation. No changes are made to the system.",
    },
    "select-all": {
        "help": "Select from all packages to remove",
        "description": "Interactively select specific packages (both active and old) to remove from the system.",
        "epilog": "You will be prompted to confirm before any packages are removed.",
    },
    "select-active": {
        "help": "Select from active packages to remove",
        "description": "Interactively select specific active packages to remove from the system.",
        "epilog": "Warning: Removing active packages will uninstall the application. You will be prompted to confirm.",
    },
    "select-old": {
        "help": "Select from old versions to remove",
        "description": "Interactively select specific old/disabled versions to remove and free up disk space.",
        "epilog": "Safe operation - only removes old versions, not active packages.",
    },
    "purge-all": {
        "help": "Remove ALL Snap packages",
        "description": "Remove every Snap package from the system - both active and old versions.",
        "epilog": "DANGER: This will remove ALL Snap packages. Use with extreme caution!",
    },
    "purge-active": {
        "help": "Remove ALL active Snap packages",
        "description": "Remove all currently active Snap packages from the system.",
        "epilog": "WARNING: This will uninstall all active Snap applications!",
    },
    "purge-old": {
        "help": "Remove ALL old Snap versions",
        "description": "Remove all old/disabled Snap versions to free up disk space.",
        "epilog": "Safe cleanup operation - only removes old versions, keeping active packages intact.",
    },
}


class CustomArgumentParser(argparse.ArgumentParser):
    """Custom parser to handle subcommand help properly."""

    def error(self, message: str) -> None:
        """Override error to show help when invalid command is given."""
        sys.stderr.write(f"Error: {message}\n\n")
        self.print_help()
        sys.exit(2)


def build_parser() -> argparse.ArgumentParser:
    parser = CustomArgumentParser(
        prog="snapout",
        description="SnapOut! - Snap Package Cleanup Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global options
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Show commands without executing (applies to remove/purge operations)"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors in terminal output"
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        metavar="COMMAND",
        help="Command to execute (omit for interactive mode)"
    )

    # Add each command as a subparser with its specific help
    for cmd, info in COMMAND_INFO.items():
        subparser = subparsers.add_parser(
            cmd,
            help=info["help"],
            description=info["description"],
            epilog=info["epilog"],
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        # Each subparser inherits the global options
        subparser.add_argument(
            "-n", "--dry-run",
            action="store_true",
            help=argparse.SUPPRESS  # Hide from subcommand help (shown in global)
        )
        subparser.add_argument(
            "--no-color",
            action="store_true",
            help=argparse.SUPPRESS  # Hide from subcommand help
        )

    return parser


def print_command_help(command: str) -> None:
    """Print detailed help for a specific command."""
    if command in COMMAND_INFO:
        info = COMMAND_INFO[command]
        print(f"\nCommand: snapout {command}")
        print("=" * 50)
        print(f"\n{info['description']}\n")
        if info['epilog']:
            print(f"Note: {info['epilog']}\n")
    else:
        print(f"Unknown command: {command}")