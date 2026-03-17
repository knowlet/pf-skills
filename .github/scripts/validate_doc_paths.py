#!/usr/bin/env python3
"""Validate that file paths referenced in skill markdown docs actually exist.

Checks two kinds of references in markdown files (outside fenced code blocks):
  1. Backtick-quoted paths that reference repo files (must contain a '/' and
     match a known repo-root prefix like skills/, .github/, commands/, etc.)
  2. Markdown links:  [label](relative/path.md)

Skips:
  - Paths inside fenced code blocks (``` ... ```)
  - Paths inside markdown headings that describe file locations in examples
  - URLs (http://, https://)
  - Paths containing template variables like {placeholder}
  - Paths that look like example/user-project references (no repo-root prefix)
"""

import os
import re
import sys
from pathlib import Path

# Known top-level directories in this repo — backtick paths must start with
# one of these to be treated as a repo-internal reference.
REPO_ROOT_PREFIXES = (
    "skills/",
    ".github/",
    ".claude-plugin/",
    "commands/",
    "agents/",
    "template/",
)

SKIP_PATTERNS = [
    re.compile(r"https?://"),      # URLs
    re.compile(r"\{[^}]+\}"),      # template variables {name}
    re.compile(r"^#"),             # anchor-only refs
    re.compile(r"^@/"),            # TS path aliases
    re.compile(r"^myapp::"),       # Rust crate paths
    re.compile(r"^node_modules/"), # node deps
]


def is_inside_code_fence(lines: list[str], target_line_idx: int) -> bool:
    """Check if a given line index is inside a fenced code block."""
    inside = False
    for i in range(target_line_idx):
        stripped = lines[i].strip()
        if stripped.startswith("```"):
            inside = not inside
    return inside


def extract_backtick_paths(line: str) -> list[str]:
    """Extract paths from single-backtick spans (not double/triple)."""
    return re.findall(r"(?<!`)`([^`]+)`(?!`)", line)


def extract_markdown_link_paths(line: str) -> list[str]:
    """Extract local file paths from markdown links [text](path)."""
    paths = []
    for match in re.finditer(r"\[([^\]]*)\]\(([^)]+)\)", line):
        target = match.group(2)
        if not target.startswith(("http://", "https://", "#", "mailto:")):
            target = target.split("#")[0]
            if target:
                paths.append(target)
    return paths


def should_skip(path: str) -> bool:
    """Check if a path should be skipped from validation."""
    for pattern in SKIP_PATTERNS:
        if pattern.search(path):
            return True
    return False


def is_repo_internal_backtick_path(path: str) -> bool:
    """Return True if a backtick-quoted path looks like a repo-internal ref.

    We only validate backtick paths that start with a known repo-root
    prefix. Everything else (bare filenames, spec-relative paths like
    ``machine/use-case.yaml``) is treated as example/documentation text.
    """
    return any(path.startswith(p) for p in REPO_ROOT_PREFIXES)


def validate_file(md_path: Path, repo_root: Path) -> list[str]:
    """Validate paths referenced in a single markdown file."""
    errors = []
    content = md_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    md_dir = md_path.parent

    for line_idx, line in enumerate(lines):
        if is_inside_code_fence(lines, line_idx):
            continue

        # --- backtick paths: only check repo-internal references ---
        for raw in extract_backtick_paths(line):
            clean = raw.rstrip(".,;:!?").split("#")[0]
            if not clean or should_skip(clean):
                continue
            if not is_repo_internal_backtick_path(clean):
                continue

            resolved = repo_root / clean
            if not resolved.exists():
                rel = md_path.relative_to(repo_root)
                errors.append(
                    f"::error file={rel},line={line_idx + 1}::"
                    f"Path not found (backtick): {clean}"
                )

        # --- markdown links: resolve relative to the file ---
        for raw in extract_markdown_link_paths(line):
            clean = raw.rstrip(".,;:!?").split("#")[0]
            if not clean or should_skip(clean):
                continue

            from_root = repo_root / clean
            from_file = md_dir / clean
            if not (from_root.exists() or from_file.exists()):
                rel = md_path.relative_to(repo_root)
                errors.append(
                    f"::error file={rel},line={line_idx + 1}::"
                    f"Path not found (link): {clean}"
                )

    return errors


def main() -> int:
    repo_root = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()

    # Scan all markdown files in the repo — not just skills/
    scan_patterns = [
        "skills/**/*.md",
        "commands/**/*.md",
        "agents/**/*.md",
        "template/**/*.md",
        "*.md",
    ]
    md_files: list[Path] = []
    for pattern in scan_patterns:
        md_files.extend(repo_root.glob(pattern))
    md_files = sorted(set(md_files))

    if not md_files:
        print("No markdown files found")
        return 1

    total_errors = 0
    total_checked = 0

    for md_path in md_files:
        errors = validate_file(md_path, repo_root)
        total_checked += 1
        if errors:
            total_errors += len(errors)
            for err in errors:
                print(err)

    print(f"\nChecked {total_checked} files, found {total_errors} broken path(s)")
    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
