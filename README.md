# SnapOut - Snap Package Cleanup Tool

Clean up old Snap package versions and reclaim disk space.

## Features

- **Scan** - See all Snap packages and old versions
- **Clean** - Remove old revisions safely
- **Interactive** - Choose what to remove with a menu
- **CLI** - Use commands directly in scripts
- **Safe** - Dry-run mode and confirmation prompts

## Quick Install

```bash
git clone https://github.com/MiguelMochizukiDev/snapout.git
cd snapout
pip install .
```

Alternatively, you can use shell script wrapper:

```bash
./snapout
```

## Usage

```bash
# Launch interactive menu
snapout

# Scan old versions (safe, read-only)
snapout scan-old

# Remove all old versions
snapout purge-old

# Preview what would be removed
snapout -n purge-old

# Remove specific old versions interactively
snapout select-old
```

## Commands

| Command | What it does |
|---------|---------------|
| `scan-all` | Show all packages |
| `scan-active` | Show active packages |
| `scan-old` | Show old versions |
| `select-old` | Choose old versions to remove |
| `purge-old` | Remove all old versions |
| `purge-active` | Remove all active packages |
| `purge-all` | Remove everything (dangerous) |

**Options:** `-n, --dry-run` (preview only), `--no-color` (disable colors)

## Why?

Snap keeps old package versions. SnapOut helps you clean them up safely.

## License

This project is under [MIT LICENSE](./LICENSE).