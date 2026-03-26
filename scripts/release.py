#!/usr/bin/env python3
"""Release script for databind packages.

Usage: python scripts/release.py <version> [--push]

1. Updates `version = "..."` in all 3 pyproject.toml files
2. Updates proxy packages' `databind>=X.Y.Z,<NEXT_MAJOR` dependency
3. Renames `.changelog/_unreleased.toml` to `.changelog/<version>.toml`, prepending `release-date`
4. Creates fresh empty `_unreleased.toml`
5. Commits, tags, optionally pushes
"""

from __future__ import annotations

import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PYPROJECT_FILES = [
    ROOT / "databind" / "pyproject.toml",
    ROOT / "databind.core" / "pyproject.toml",
    ROOT / "databind.json" / "pyproject.toml",
]

PROXY_PACKAGES = [
    ROOT / "databind.core" / "pyproject.toml",
    ROOT / "databind.json" / "pyproject.toml",
]

CHANGELOG_DIR = ROOT / ".changelog"


def update_version(path: Path, version: str) -> None:
    text = path.read_text()
    new_text = re.sub(r'^(version\s*=\s*)"[^"]*"', rf'\1"{version}"', text, count=1, flags=re.MULTILINE)
    if new_text == text:
        print(f"  WARNING: no version line found in {path}", file=sys.stderr)
    path.write_text(new_text)


def next_major(version: str) -> str:
    major = int(version.split(".")[0]) + 1
    return str(major)


def update_proxy_dependency(path: Path, version: str) -> None:
    text = path.read_text()
    new_dep = f'"databind>={version},<{next_major(version)}"'
    new_text = re.sub(r'"databind>=[\d.]+,<\d+"', new_dep, text)
    path.write_text(new_text)


def rename_changelog(version: str) -> None:
    unreleased = CHANGELOG_DIR / "_unreleased.toml"
    target = CHANGELOG_DIR / f"{version}.toml"
    if not unreleased.exists():
        print(f"  WARNING: {unreleased} does not exist", file=sys.stderr)
        return
    if target.exists():
        print(f"  ERROR: {target} already exists", file=sys.stderr)
        sys.exit(1)

    content = unreleased.read_text()
    today = datetime.date.today().isoformat()
    target.write_text(f'release-date = "{today}"\n\n{content}')
    unreleased.write_text("")


def git(*args: str) -> None:
    cmd = ["git", "-C", str(ROOT), *args]
    print(f"  $ {' '.join(cmd)}")
    subprocess.check_call(cmd)


def main() -> None:
    parser = argparse.ArgumentParser(description="Release databind packages")
    parser.add_argument("version", help="Version to release (e.g. 4.6.0)")
    parser.add_argument("--push", action="store_true", help="Push commit and tag to origin")
    args = parser.parse_args()

    version: str = args.version

    print(f"Releasing version {version}")

    print("\n1. Updating versions in pyproject.toml files...")
    for path in PYPROJECT_FILES:
        print(f"  {path.relative_to(ROOT)}")
        update_version(path, version)

    print("\n2. Updating proxy package dependencies...")
    for path in PROXY_PACKAGES:
        print(f"  {path.relative_to(ROOT)}")
        update_proxy_dependency(path, version)

    print("\n3. Renaming changelog...")
    rename_changelog(version)

    print("\n4. Updating lockfile...")
    subprocess.check_call(["uv", "lock"], cwd=str(ROOT))

    print("\n5. Committing and tagging...")
    git("add", "-A")
    git("commit", "-m", f"Release {version}")
    git("tag", version)

    if args.push:
        print("\n6. Pushing...")
        git("push", "origin", "HEAD", version)
    else:
        print(f"\nDone. Run 'git push origin HEAD {version}' to push.")


if __name__ == "__main__":
    main()
