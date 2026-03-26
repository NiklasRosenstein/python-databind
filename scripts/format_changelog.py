#!/usr/bin/env python3
"""Format all changelog entries as markdown.

Reads `.changelog/*.toml` files (excluding `_unreleased.toml` if empty),
sorts by version descending, and outputs markdown to stdout.

Replaces `slap changelog format --markdown --all`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redefine]

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG_DIR = ROOT / ".changelog"


def version_sort_key(name: str) -> tuple:
    """Sort key that handles semver-like versions including pre-release tags."""
    # Strip .toml extension
    name = name.removesuffix(".toml")

    if name == "_unreleased":
        # Sort unreleased first (highest)
        return ((1, 999999),)

    # Split on dots and hyphens, convert numeric parts to ints
    parts = re.split(r"[.\-]", name)
    result = []
    for part in parts:
        if part.isdigit():
            result.append((1, int(part)))
        else:
            # Pre-release tags sort lower than release versions
            result.append((0, ord(part[0]) if part else 0))
    return tuple(result)


def format_entry(entry: dict) -> str:
    entry_type = entry.get("type", "change")
    description = entry.get("description", "")
    pr = entry.get("pr", "")
    author = entry.get("author", "")

    suffix_parts = []
    if pr:
        suffix_parts.append(pr)
    if author:
        suffix_parts.append(author)
    suffix = f" ({', '.join(suffix_parts)})" if suffix_parts else ""

    return f"- **{entry_type}**: {description}{suffix}"


def main() -> None:
    changelog_files = sorted(CHANGELOG_DIR.glob("*.toml"), key=lambda p: version_sort_key(p.name), reverse=True)

    if not changelog_files:
        print("No changelog files found.", file=sys.stderr)
        sys.exit(1)

    first = True
    for path in changelog_files:
        data = tomllib.loads(path.read_text())
        entries = data.get("entries", [])

        name = path.stem
        if name == "_unreleased":
            if not entries:
                continue
            heading = "Unreleased"
        else:
            release_date = data.get("release-date", "")
            heading = f"{name} ({release_date})" if release_date else name

        if not first:
            print()
        first = False

        print(f"## {heading}\n")
        if entries:
            for entry in entries:
                print(format_entry(entry))
        else:
            print("No changes.")


if __name__ == "__main__":
    main()
