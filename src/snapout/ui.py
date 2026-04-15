"""
ui.py
Console rendering and input handling for SnapOut.
"""

from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

from .core import SnapRow


C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_RED = "\033[31m"
C_GREEN = "\033[32m"
C_YELLOW = "\033[33m"
C_BLUE = "\033[34m"
C_CYAN = "\033[36m"
C_WHITE = "\033[37m"
C_GRAY = "\033[90m"


def _supports_color() -> bool:
    if os.getenv("NO_COLOR") is not None:
        return False
    if os.getenv("SNAPOUT_NO_COLOR", "").lower() in {"1", "true", "yes"}:
        return False
    if os.getenv("TERM", "") == "dumb":
        return False
    return sys.stdout.isatty()


class ConsoleUI:
    def __init__(self, auto_clear: bool | None = None, use_color: bool | None = None) -> None:
        if auto_clear is None:
            auto_clear = os.getenv("SNAPOUT_AUTO_CLEAR", "true").lower() == "true"
        if use_color is None:
            use_color = _supports_color()
        self.auto_clear = auto_clear
        self.use_color = use_color

        self.reset = C_RESET if use_color else ""
        self.bold = C_BOLD if use_color else ""
        self.dim = C_DIM if use_color else ""
        self.red = C_RED if use_color else ""
        self.green = C_GREEN if use_color else ""
        self.yellow = C_YELLOW if use_color else ""
        self.blue = C_BLUE if use_color else ""
        self.cyan = C_CYAN if use_color else ""
        self.white = C_WHITE if use_color else ""
        self.gray = C_GRAY if use_color else ""

    def style(self, text: str, color: str = "") -> str:
        return f"{color}{text}{self.reset}"

    def _print_color(self, color: str, text: str) -> None:
        print(self.style(text, color))

    def print_bold(self, text: str) -> None:
        print(self.style(text, self.bold))

    def clear_screen(self, cli_mode: bool) -> None:
        if cli_mode or not self.auto_clear:
            return
        os.system("clear")

    def header(self, cli_mode: bool) -> None:
        self.clear_screen(cli_mode)
        print()
        self._print_color(self.cyan, "==================================================")
        self._print_color(self.cyan + self.bold, "  SnapOut! - Snap Package Cleanup Tool")
        self._print_color(self.cyan, "==================================================")
        print()

    def section(self, title: str, cli_mode: bool) -> None:
        if cli_mode:
            return
        print()
        self._print_color(self.blue, "--------------------------------------------------")
        self._print_color(self.bold + self.cyan, f"  {title}")
        self._print_color(self.blue, "--------------------------------------------------")
        print()

    def show_active(self, rows: list[SnapRow], show_indices: bool = True) -> None:
        if show_indices:
            print(f"  {self.bold}{'#':<4} {'Name':<20} {'Version':<15} {'Revision':<10} Notes{self.reset}")
            self._print_color(self.gray, "  ------------------------------------------------------------------")
            for idx, row in enumerate(rows, start=1):
                print(
                    f"  {self.dim}{idx:<4}{self.reset} "
                    f"{self.white}{row.name:<20}{self.reset} "
                    f"{self.cyan}{row.version:<15}{self.reset} "
                    f"{self.yellow}{row.revision:<10}{self.reset} "
                    f"{self.dim}active{self.reset}"
                )
        else:
            print(f"  {self.bold}{'Name':<20} {'Version':<15} {'Revision':<10} Notes{self.reset}")
            self._print_color(self.gray, "  ------------------------------------------------------------------")
            for row in rows:
                print(
                    f"  {self.white}{row.name:<20}{self.reset} "
                    f"{self.cyan}{row.version:<15}{self.reset} "
                    f"{self.yellow}{row.revision:<10}{self.reset} "
                    f"{self.dim}active{self.reset}"
                )
        print()
        self._print_color(self.blue, f"  Total: {len(rows)} packages")
        print()

    def show_old(self, rows: list[SnapRow]) -> None:
        print(f"  {self.bold}{'#':<4} {'Name':<20} {'Revision':<10} {'Size':<10} Status{self.reset}")
        self._print_color(self.gray, "  -----------------------------------------------------")

        total_size = 0
        for idx, row in enumerate(rows, start=1):
            size_bytes = self._get_revision_size_bytes(row.name, row.revision)
            total_size += size_bytes
            size_str = self._format_size(size_bytes)

            print(
                f"  {self.dim}{idx:<4}{self.reset} "
                f"{self.white}{row.name:<20}{self.reset} "
                f"{self.yellow}{row.revision:<10}{self.reset} "
                f"{self.cyan}{size_str:<10}{self.reset} "
                f"{self.red}disabled{self.reset}"
            )
        print()
        self._print_color(self.yellow, f"  Found {len(rows)} old versions")

        if total_size > 0:
            size_str = self._format_size(total_size)
            self._print_color(self.green, f"  💾 Potential space savings: {size_str}")

        print()
        counts = Counter(row.name for row in rows)
        if counts:
            self._print_color(self.dim, "  Package summary:")
            for name, count in sorted(counts.items()):
                print(f"  {self.white}{name:<20}{self.reset} {self.dim}{count} version(s){self.reset}")
        print()

    def _get_revision_size_bytes(self, name: str, revision: str) -> int:
        """Get size of a snap revision in bytes."""
        snap_path = Path(f"/var/lib/snapd/snaps/{name}_{revision}.snap")
        try:
            return snap_path.stat().st_size if snap_path.exists() else 0
        except OSError:
            return 0

    def _format_size(self, size_bytes: int) -> str:
        """Format bytes to human readable size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def show_progress_bar(self, current: int, total: int, label: str, width: int = 30) -> None:
        """Display a progress bar."""
        percent = current / total
        filled = int(width * percent)
        bar = '█' * filled + '░' * (width - filled)
        print(f"\r  {self.cyan}[{bar}]{self.reset} {current}/{total} {label}", end='', flush=True)

    def show_progress_complete(self, current: int, total: int, label: str, success: bool = True) -> None:
        """Complete the progress bar with success/failure indicator."""
        symbol = f"{self.green}✓{self.reset}" if success else f"{self.red}✗{self.reset}"
        print(f"\r  {symbol} {current}/{total} {label}" + " " * 20)

    def show_smart_suggestions(self, rows: list[SnapRow]) -> None:
        """Show smart cleanup suggestions."""
        from collections import Counter
        counts = Counter(row.name for row in rows)

        suggestions = []
        for name, count in counts.items():
            if count > 3:
                suggestions.append((name, count))

        if suggestions:
            print()
            self._print_color(self.yellow + self.bold, "  💡 Smart Suggestions:")
            self._print_color(self.dim, "     These packages have many old versions. Consider cleaning them up:")
            for name, count in sorted(suggestions, key=lambda x: x[1], reverse=True):
                # Calculate total size for this package
                pkg_rows = [r for r in rows if r.name == name]
                pkg_size = sum(self._get_revision_size_bytes(r.name, r.revision) for r in pkg_rows)
                size_str = self._format_size(pkg_size)
                print(f"    • {self.white}{name:<20}{self.reset} {self.dim}{count} old versions{self.reset} ({self.cyan}{size_str}{self.reset})")

    def input(self, prompt: str) -> str:
        return input(prompt).strip()

    def input_menu_choice(self) -> str:
        return self.input(f"  {self.green}Select option{self.reset} {self.dim}[0-9]{self.reset} ")

    def input_mode(self) -> str:
        return self.input(f"  {self.green}>{self.reset} ").lower()

    def input_selection(self, rows: list[SnapRow], prompt: str) -> tuple[list[SnapRow], str]:
        print()
        print(f"{self.dim}  Enter numbers separated by commas (ex: 1,3,5){self.reset}")
        print(f"{self.dim}  Range support: 1-5 selects items 1 through 5{self.reset}")
        choice = self.input(f"  {self.green}{prompt}{self.reset} ")
        if not choice:
            return [], "invalid"
        if choice.lower() == "q":
            return [], "quit"

        selected_indices: set[int] = set()
        for token in choice.split(","):
            token = token.strip()
            if not token:
                continue
            if token.lower() == "q":
                return [], "quit"
            if "-" in token:
                # Handle range like "1-5"
                try:
                    start, end = map(int, token.split("-"))
                    selected_indices.update(range(start, end + 1))
                except ValueError:
                    continue
            elif token.isdigit():
                selected_indices.add(int(token))

        selected = [row for idx, row in enumerate(rows, start=1) if idx in selected_indices]
        if not selected:
            return [], "invalid"
        return selected, "ok"

    def confirm(self, message: str) -> str:
        answer = self.input(f"{self.yellow}{message} (y/N){self.reset} ").lower()
        if answer == "q":
            return "quit"
        if answer == "y":
            return "yes"
        return "no"

    def confirm_yes_word(self, message: str, expected: str = "YES") -> str:
        answer = self.input(f"{self.yellow}{message}{self.reset}")
        if answer.lower() == "q":
            return "quit"
        if answer == expected:
            return "yes"
        return "no"

    def pause_or_quit(self) -> bool:
        nxt = self.input(f"{self.gray}Press Enter to continue (or 'q' to quit)...{self.reset} ").lower()
        return nxt == "q"

    def cancel(self) -> None:
        self._print_color(self.blue, "  Operation canceled")

    def info(self, message: str) -> None:
        self._print_color(self.cyan, message)

    def warn(self, message: str) -> None:
        self._print_color(self.yellow, message)

    def success(self, message: str) -> None:
        self._print_color(self.green, message)

    def error(self, message: str) -> None:
        self._print_color(self.red, message)

    def goodbye(self) -> None:
        self.clear_screen(cli_mode=False)
        print()
        self._print_color(self.cyan, "  Goodbye!")
        print()

    def interrupted(self) -> None:
        self.clear_screen(cli_mode=False)
        print()
        self._print_color(self.cyan, "  Interrupted. Goodbye!")
        print()