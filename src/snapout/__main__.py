"""
__main__.py
Thin entrypoint for SnapOut composition and execution.
"""

from __future__ import annotations

import shutil
import sys

from .application import CoreSnapOperations, SnapoutApplication
from .cli import build_parser, print_command_help
from .ui import ConsoleUI


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()

    # Check if user wants help for a specific command
    if argv and len(argv) >= 2 and argv[0] in ["--help", "-h"]:
        # snapout --help scan-all
        print_command_help(argv[1])
        return 0
    elif argv and "--help" in argv:
        # snapout scan-all --help
        cmd_idx = argv.index("--help") - 1
        if cmd_idx >= 0:
            print_command_help(argv[cmd_idx])
            return 0
    elif argv and "-h" in argv:
        # snapout scan-all -h
        cmd_idx = argv.index("-h") - 1
        if cmd_idx >= 0:
            print_command_help(argv[cmd_idx])
            return 0

    args = parser.parse_args(argv)

    ui = ConsoleUI(use_color=not args.no_color)

    if shutil.which("snap") is None:
        ui.error("Error: snap command not found")
        return 1

    app = SnapoutApplication(ops=CoreSnapOperations(), ui=ui, dry_run=args.dry_run)

    # Run command or interactive mode
    if args.command:
        result = app.run_command(args.command, cli_mode=True)
        return result.code
    else:
        return app.run_interactive()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))