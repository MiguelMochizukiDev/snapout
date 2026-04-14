"""
application.py
Application use-cases and action registry for SnapOut.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .core import SnapRow, active_snap_rows, old_snap_rows, snap_rows, remove_package, remove_revision
from .ui import ConsoleUI


class SnapOperations(Protocol):
    def all_rows(self) -> list[SnapRow]:
        ...

    def active_rows(self) -> list[SnapRow]:
        ...

    def old_rows(self) -> list[SnapRow]:
        ...

    def remove_package(self, name: str, dry_run: bool) -> int:
        ...

    def remove_revision(self, name: str, revision: str, dry_run: bool) -> int:
        ...


class CoreSnapOperations:
    def all_rows(self) -> list[SnapRow]:
        return snap_rows()

    def active_rows(self) -> list[SnapRow]:
        return active_snap_rows()

    def old_rows(self) -> list[SnapRow]:
        return old_snap_rows()

    def remove_package(self, name: str, dry_run: bool) -> int:
        return remove_package(name, dry_run=dry_run)

    def remove_revision(self, name: str, revision: str, dry_run: bool) -> int:
        return remove_revision(name, revision, dry_run=dry_run)


@dataclass(frozen=True)
class ActionResult:
    code: int = 0
    skip_continue_prompt: bool = False


class SnapoutApplication:
    def __init__(self, ops: SnapOperations, ui: ConsoleUI, dry_run: bool) -> None:
        self.ops = ops
        self.ui = ui
        self.dry_run = dry_run

    def run_command(self, command: str, cli_mode: bool = False) -> ActionResult:
        """Execute a specific command."""
        handlers = {
            "scan-all": self.scan_all,
            "scan-active": self.scan_active,
            "scan-old": self.scan_old,
            "select-all": self.select_all,
            "select-active": self.select_active,
            "select-old": self.select_old,
            "purge-all": self.purge_all,
            "purge-active": self.purge_active,
            "purge-old": self.purge_old,
        }

        handler = handlers.get(command)
        if not handler:
            self.ui.error(f"Unknown command: {command}")
            return ActionResult(code=1)

        result = handler(cli_mode=cli_mode)
        return result

    def scan_all(self, cli_mode: bool) -> ActionResult:
        """Scan all Snap packages (active and old)."""
        self.ui.header(cli_mode)
        self.ui.section("All Snap Packages", cli_mode)
        rows = self.ops.all_rows()
        if not rows:
            self.ui.warn("  No Snap packages found")
            print()
            return ActionResult(code=0, skip_continue_prompt=False)

        # Split into active and old for better display
        active = [r for r in rows if r.notes != "disabled"]
        old = [r for r in rows if r.notes == "disabled"]

        if active:
            self.ui.section(f"Active Packages ({len(active)})", cli_mode)
            self.ui.show_active(active)

        if old:
            self.ui.section(f"Old Versions ({len(old)})", cli_mode)
            self.ui.show_old(old)
            # Show smart suggestions for old versions
            self.ui.show_smart_suggestions(old)

        if not active and not old:
            self.ui.success("  No Snap packages found")

        return ActionResult(code=0, skip_continue_prompt=False)

    def scan_active(self, cli_mode: bool) -> ActionResult:
        """Scan only active Snap packages."""
        self.ui.header(cli_mode)
        self.ui.section("Active Snap Packages", cli_mode)
        rows = self.ops.active_rows()
        if not rows:
            self.ui.warn("  No active Snap packages found")
            print()
            return ActionResult(code=0, skip_continue_prompt=False)
        self.ui.show_active(rows)
        return ActionResult(code=0, skip_continue_prompt=False)

    def scan_old(self, cli_mode: bool) -> ActionResult:
        """Scan only old Snap versions."""
        self.ui.header(cli_mode)
        self.ui.section("Old Snap Versions", cli_mode)
        rows = self.ops.old_rows()
        if not rows:
            self.ui.success("  No old versions found - system is clean!")
            print()
            return ActionResult(code=0, skip_continue_prompt=False)
        self.ui.show_old(rows)
        # Show smart suggestions
        self.ui.show_smart_suggestions(rows)
        return ActionResult(code=0, skip_continue_prompt=False)

    def select_all(self, cli_mode: bool) -> ActionResult:
        """Select from all packages to remove."""
        self.ui.header(cli_mode)
        self.ui.section("Select Packages to Remove (All)", cli_mode)
        rows = self.ops.all_rows()
        if not rows:
            self.ui.success("  No Snap packages found")
            return ActionResult()

        return self._interactive_selection(rows, "all")

    def select_active(self, cli_mode: bool) -> ActionResult:
        """Select from active packages to remove."""
        self.ui.header(cli_mode)
        self.ui.section("Select Packages to Remove (Active Only)", cli_mode)
        rows = self.ops.active_rows()
        if not rows:
            self.ui.success("  No active Snap packages to remove")
            return ActionResult()

        return self._interactive_selection(rows, "active")

    def select_old(self, cli_mode: bool) -> ActionResult:
        """Select from old versions to remove."""
        self.ui.header(cli_mode)
        self.ui.section("Select Old Versions to Remove", cli_mode)
        rows = self.ops.old_rows()
        if not rows:
            self.ui.success("  No old versions to remove")
            return ActionResult()

        return self._interactive_selection(rows, "old")

    def purge_all(self, cli_mode: bool) -> ActionResult:
        """Remove ALL Snap packages."""
        self.ui.header(cli_mode)
        self.ui.section("Remove ALL Snap Packages", cli_mode)
        rows = self.ops.all_rows()
        if not rows:
            self.ui.success("  No Snap packages to remove")
            return ActionResult()

        return self._confirm_and_purge(rows, "ALL Snap packages (active AND old)")

    def purge_active(self, cli_mode: bool) -> ActionResult:
        """Remove ALL active Snap packages."""
        self.ui.header(cli_mode)
        self.ui.section("Remove ALL Active Snap Packages", cli_mode)
        rows = self.ops.active_rows()
        if not rows:
            self.ui.success("  No active Snap packages to remove")
            return ActionResult()

        return self._confirm_and_purge(rows, "ALL active Snap packages")

    def purge_old(self, cli_mode: bool) -> ActionResult:
        """Remove ALL old Snap versions."""
        self.ui.header(cli_mode)
        self.ui.section("Remove ALL Old Snap Versions", cli_mode)
        rows = self.ops.old_rows()
        if not rows:
            self.ui.success("  No old versions to remove")
            return ActionResult()

        return self._confirm_and_purge(rows, "ALL old Snap versions")

    def _interactive_selection(self, rows: list[SnapRow], category: str) -> ActionResult:
        """Handle interactive selection and removal."""
        # Separate active and old if showing all
        if category == "all":
            active = [r for r in rows if r.notes != "disabled"]
            old = [r for r in rows if r.notes == "disabled"]
            if active:
                self.ui.show_active(active)
            if old:
                self.ui.show_old(old)
                self.ui.show_smart_suggestions(old)
        elif category == "active":
            self.ui.show_active(rows)
        else:  # old
            self.ui.show_old(rows)
            self.ui.show_smart_suggestions(rows)

        if len(rows) == 1:
            return self._handle_single_selection(rows[0], category)

        print()
        self.ui.info("  Options: [s]elect numbers | [a]ll | [q]uit")
        mode = self.ui.input_mode()

        if mode == "q":
            return ActionResult(skip_continue_prompt=True)
        if mode == "a":
            if category == "old":
                return self.purge_old(cli_mode=False)
            elif category == "active":
                return self.purge_active(cli_mode=False)
            else:
                return self.purge_all(cli_mode=False)
        if mode != "s":
            self.ui.warn("  Invalid option")
            return ActionResult()

        selected, status = self.ui.input_selection(rows, "Selection")
        if status == "quit":
            return ActionResult(skip_continue_prompt=True)
        if status != "ok":
            self.ui.warn("  No valid selection")
            return ActionResult()

        print()
        self.ui.print_bold("  About to remove:")
        total_size = 0
        for row in selected:
            if category == "old":
                size_bytes = self.ui._get_revision_size_bytes(row.name, row.revision)
                total_size += size_bytes
                size_str = self.ui._format_size(size_bytes)
                print(f"  {self.ui.white}{row.name:<20}{self.ui.reset} revision {self.ui.yellow}{row.revision}{self.ui.reset} ({self.ui.cyan}{size_str}{self.ui.reset})")
            else:
                print(f"  {self.ui.white}{row.name}{self.ui.reset}")

        if total_size > 0:
            print(f"\n  {self.ui.green}💾 Total space to free: {self.ui._format_size(total_size)}{self.ui.reset}")

        if self.ui.confirm("Proceed?") != "yes":
            self.ui.cancel()
            return ActionResult()

        # Determine if we're removing packages or revisions
        if category == "old":
            return self._remove_revisions_with_progress(selected)
        else:
            return self._remove_packages_with_progress(selected)

    def _handle_single_selection(self, row: SnapRow, category: str) -> ActionResult:
        """Handle removal of a single item."""
        if category == "old":
            size_bytes = self.ui._get_revision_size_bytes(row.name, row.revision)
            size_str = self.ui._format_size(size_bytes)
            self.ui.info(f"  Only one old version: {row.name} (rev {row.revision}) - {size_str}")
            confirm = self.ui.confirm("Remove automatically?")
            if confirm != "yes":
                self.ui.cancel()
                return ActionResult(skip_continue_prompt=(confirm == "quit"))
            rc = self.ops.remove_revision(row.name, row.revision, dry_run=self.dry_run)
            if rc == 0:
                self.ui.success(f"  [OK] Removed {row.name} revision {row.revision} ({size_str})")
            else:
                self.ui.error("  [FAIL] Failed")
            return ActionResult(code=rc)
        else:
            self.ui.info(f"  Only one package: {row.name}")
            confirm = self.ui.confirm("Remove automatically?")
            if confirm != "yes":
                self.ui.cancel()
                return ActionResult(skip_continue_prompt=(confirm == "quit"))
            rc = self.ops.remove_package(row.name, dry_run=self.dry_run)
            if rc == 0:
                self.ui.success(f"  [OK] Removed {row.name}")
            else:
                self.ui.error("  [FAIL] Failed")
            return ActionResult(code=rc)

    def _confirm_and_purge(self, rows: list[SnapRow], description: str) -> ActionResult:
        """Confirm and execute purge operation."""
        self.ui.error(f"  WARNING: This will remove {description}!")
        if any(r.notes != "disabled" for r in rows):
            self.ui.error("  This action CANNOT be undone!")
        print()

        self.ui.print_bold("  Items to be removed:")
        total_size = 0
        for row in rows:
            if row.notes == "disabled":
                size_bytes = self.ui._get_revision_size_bytes(row.name, row.revision)
                total_size += size_bytes
                size_str = self.ui._format_size(size_bytes)
                print(f"  {self.ui.white}{row.name:<20}{self.ui.reset} revision {self.ui.yellow}{row.revision}{self.ui.reset} ({self.ui.cyan}{size_str}{self.ui.reset}) (old)")
            else:
                print(f"  {self.ui.white}{row.name}{self.ui.reset} (active)")

        if total_size > 0:
            print(f"\n  {self.ui.green}💾 Total space to free: {self.ui._format_size(total_size)}{self.ui.reset}")

        print()
        confirm = self.ui.confirm_yes_word("  Type 'YES' to confirm (or 'q' to quit): ")
        if confirm != "yes":
            if confirm == "no":
                self.ui.cancel()
            return ActionResult(skip_continue_prompt=(confirm == "quit"))

        # Check if we're removing old versions or packages
        if all(r.notes == "disabled" for r in rows):
            return self._remove_revisions_with_progress(rows)
        else:
            return self._remove_packages_with_progress(rows)

    def _remove_packages_with_progress(self, rows: list[SnapRow]) -> ActionResult:
        """Remove packages with progress display."""
        removed = 0
        total = len(rows)

        for idx, row in enumerate(rows, start=1):
            self.ui.show_progress_bar(idx - 1, total, f"Removing {row.name}...")
            rc = self.ops.remove_package(row.name, dry_run=self.dry_run)
            success = rc == 0
            if success:
                removed += 1
            self.ui.show_progress_complete(idx, total, f"Removed {row.name}", success)

        print()
        self.ui.success(f"  [OK] Removed {removed}/{total} packages")
        return ActionResult()

    def _remove_revisions_with_progress(self, rows: list[SnapRow]) -> ActionResult:
        """Remove old revisions with progress display."""
        removed = 0
        total = len(rows)

        for idx, row in enumerate(rows, start=1):
            label = f"Removing {row.name} (rev {row.revision})"
            self.ui.show_progress_bar(idx - 1, total, label)
            rc = self.ops.remove_revision(row.name, row.revision, dry_run=self.dry_run)
            success = rc == 0
            if success:
                removed += 1
            self.ui.show_progress_complete(idx, total, f"Removed {row.name} rev {row.revision}", success)

        print()
        self.ui.success(f"  [OK] Removed {removed}/{total} old versions")
        return ActionResult()

    def run_interactive(self) -> int:
        """Run in interactive menu mode."""
        try:
            while True:
                self._show_interactive_menu()
                choice = self.ui.input_menu_choice()
                if choice.lower() in {"0", "q"}:
                    self.ui.goodbye()
                    return 0

                # Map menu choices to commands
                menu_map = {
                    "1": "scan-all",
                    "2": "scan-active",
                    "3": "scan-old",
                    "4": "select-all",
                    "5": "select-active",
                    "6": "select-old",
                    "7": "purge-all",
                    "8": "purge-active",
                    "9": "purge-old",
                }

                command = menu_map.get(choice)
                if not command:
                    self.ui.warn("  Invalid option")
                    continue

                result = self.run_command(command, cli_mode=False)
                if not result.skip_continue_prompt and self.ui.pause_or_quit():
                    self.ui.goodbye()
                    return 0
        except KeyboardInterrupt:
            self.ui.interrupted()
            return 0

    def _show_interactive_menu(self) -> None:
        """Display the interactive menu."""
        self.ui.header(cli_mode=False)

        # Show quick dashboard
        all_rows = self.ops.all_rows()
        active_count = len([r for r in all_rows if r.notes != "disabled"])
        old_count = len([r for r in all_rows if r.notes == "disabled"])

        if old_count > 0:
            old_rows = self.ops.old_rows()
            total_size = sum(self.ui._get_revision_size_bytes(r.name, r.revision) for r in old_rows)
            size_str = self.ui._format_size(total_size)
            print(f"  {self.ui.dim}Dashboard: {self.ui.white}{active_count}{self.ui.dim} active, {self.ui.yellow}{old_count}{self.ui.dim} old versions ({self.ui.cyan}{size_str}{self.ui.dim} reclaimable){self.ui.reset}")
            print()

        # Scan Operations Section
        print(f"  {self.ui.bold}{self.ui.cyan}Scan Operations{self.ui.reset}")
        self._print_menu_item("1", "Scan all packages", "Scan ALL Snap packages (active + old)")
        self._print_menu_item("2", "Scan active only", "Scan only active Snap packages")
        self._print_menu_item("3", "Scan old only", "Scan only old Snap versions")
        print()

        # Selection Operations Section
        print(f"  {self.ui.bold}{self.ui.cyan}Selection Operations{self.ui.reset}")
        self._print_menu_item("4", "Select from all", "Select from all packages to remove")
        self._print_menu_item("5", "Select from active", "Select from active packages to remove")
        self._print_menu_item("6", "Select from old", "Select from old versions to remove")
        print()

        # Purge Operations Section
        print(f"  {self.ui.bold}{self.ui.cyan}Purge Operations{self.ui.reset}")
        self._print_menu_item("7", "Purge all", "Remove ALL Snap packages (DANGER!)")
        self._print_menu_item("8", "Purge active", "Remove ALL active Snap packages")
        self._print_menu_item("9", "Purge old", "Remove ALL old Snap versions")
        print()

        # Exit Option
        self._print_menu_item("0", "Exit", "Quit SnapOut")
        print()

        # Divider line using public method
        self.ui.info("  -------------------------------------------------")
        print()

    def _print_menu_item(self, key: str, label: str, description: str) -> None:
        """Print a formatted menu item."""
        print(f"  {self.ui.bold}{self.ui.white}[{key}]{self.ui.reset} {self.ui.white}{label:<20}{self.ui.reset} {self.ui.dim}{description}{self.ui.reset}")