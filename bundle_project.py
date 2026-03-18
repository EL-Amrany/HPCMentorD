#!/usr/bin/env python3
"""
bundle_project.py
Create a single "bundle" file from a project folder:
- Writes an ASCII tree of included files first (project structure)
- Then writes each file with a clear path header and its contents

Usage:
  python bundle_project.py /path/to/flask_project -o bundle.md --format markdown
  python bundle_project.py . -o bundle.txt --format plain
"""

from __future__ import annotations

import argparse
import fnmatch
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional


DEFAULT_EXCLUDES = [
    # VCS / IDE
    ".git", ".hg", ".svn", ".idea", ".vscode",
    # Python caches / tooling
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    "*.pyc", "*.pyo", "*.pyd",
    # Virtual envs
    "venv", "env", ".venv",
    # Node / front-end
    "node_modules", "dist", "build",
    # OS
    ".DS_Store", "Thumbs.db",
    # Logs / data
    "*.log", "*.sqlite", "*.sqlite3", "*.db",
    # Secrets / certs
    ".env", ".env.*", "*.env", "*.pem", "*.key", "*.crt",
    # Flask instance often contains secrets/config overrides
    "instance",
]


EXT_TO_LANG = {
    ".py": "python",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".js": "javascript",
    ".ts": "typescript",
    ".json": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".md": "markdown",
    ".txt": "text",
    ".ini": "ini",
    ".cfg": "ini",
    ".toml": "toml",
    ".sh": "bash",
    ".dockerfile": "dockerfile",
}


def is_binary_file(path: Path, sniff_bytes: int = 8192) -> bool:
    try:
        data = path.read_bytes()[:sniff_bytes]
    except Exception:
        return True
    if b"\x00" in data:
        return True
    # Heuristic: if many bytes are outside typical text range, treat as binary
    # (still allows UTF-8 text; we only do a rough check)
    textish = sum(1 for b in data if b in b"\t\n\r" or 32 <= b <= 126)
    return len(data) > 0 and (textish / len(data)) < 0.70


def matches_any(name_or_path: str, patterns: List[str]) -> bool:
    return any(fnmatch.fnmatch(name_or_path, pat) for pat in patterns)


def should_exclude(rel_path: str, excludes: List[str]) -> bool:
    parts = rel_path.split("/")
    # Exclude if any directory name matches an exclude pattern (like ".git", "venv")
    for i in range(len(parts)):
        chunk = parts[i]
        if matches_any(chunk, excludes):
            return True
    # Exclude if full relative path matches a glob pattern (like "*.pyc", ".env")
    if matches_any(rel_path, excludes):
        return True
    return False


def collect_files(root: Path, excludes: List[str], include_hidden: bool) -> List[Path]:
    files: List[Path] = []
    root = root.resolve()

    for dirpath, dirnames, filenames in os.walk(root):
        dp = Path(dirpath)

        # Optionally skip hidden dirs (that start with ".") unless include_hidden
        if not include_hidden:
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]

        # Prune excluded directories early
        pruned = []
        for d in list(dirnames):
            rel_dir = (dp / d).relative_to(root).as_posix()
            if should_exclude(rel_dir, excludes):
                pruned.append(d)
        for d in pruned:
            dirnames.remove(d)

        for fn in filenames:
            if not include_hidden and fn.startswith("."):
                continue
            p = dp / fn
            rel = p.relative_to(root).as_posix()
            if should_exclude(rel, excludes):
                continue
            files.append(p)

    files.sort(key=lambda p: p.relative_to(root).as_posix().lower())
    return files


def build_tree(paths: List[str]) -> Dict:
    tree: Dict = {}
    for p in paths:
        node = tree
        parts = p.split("/")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node.setdefault("__files__", []).append(parts[-1])
    return tree


def render_tree(tree: Dict, prefix: str = "") -> str:
    # Renders directories and files in a stable, readable order
    out_lines: List[str] = []

    dirs = sorted([k for k in tree.keys() if k != "__files__"])
    files = sorted(tree.get("__files__", []))

    entries: List[Tuple[str, Optional[Dict]]] = [(d, tree[d]) for d in dirs] + [(f, None) for f in files]

    for i, (name, subtree) in enumerate(entries):
        is_last = (i == len(entries) - 1)
        branch = "└── " if is_last else "├── "
        out_lines.append(prefix + branch + name)
        if subtree is not None:
            extension = "    " if is_last else "│   "
            out_lines.extend(render_tree(subtree, prefix + extension).splitlines())

    return "\n".join(out_lines)


def guess_language(path: Path) -> str:
    ext = path.suffix.lower()
    if path.name.lower() == "dockerfile":
        return "dockerfile"
    return EXT_TO_LANG.get(ext, "")


def write_bundle(
    root: Path,
    files: List[Path],
    out_path: Path,
    out_format: str,
    max_bytes: int,
) -> None:
    root = root.resolve()
    out_path = out_path.resolve()

    # Avoid including the output file itself if it's inside the root
    filtered_files = []
    for p in files:
        try:
            if p.resolve() == out_path:
                continue
        except Exception:
            pass
        filtered_files.append(p)

    rel_paths = [p.relative_to(root).as_posix() for p in filtered_files]
    tree = build_tree(rel_paths)
    tree_text = render_tree(tree)

    with out_path.open("w", encoding="utf-8", newline="\n") as out:
        if out_format == "markdown":
            out.write(f"# Project bundle\n\n")
            out.write(f"## Structure\n\n```text\n{tree_text}\n```\n\n")
        else:
            out.write("PROJECT BUNDLE\n\n")
            out.write("STRUCTURE:\n")
            out.write(tree_text + "\n\n")

        for p in filtered_files:
            rel = p.relative_to(root).as_posix()
            try:
                size = p.stat().st_size
            except Exception:
                size = -1

            header = f"{rel}  (size: {size} bytes)"
            if out_format == "markdown":
                out.write(f"---\n\n## FILE: `{rel}`\n\n")
            else:
                out.write("=" * 80 + "\n")
                out.write(f"FILE: {header}\n")
                out.write("=" * 80 + "\n")

            if size >= 0 and size > max_bytes:
                msg = f"[SKIPPED: file too large > {max_bytes} bytes]\n\n"
                out.write(msg)
                continue

            if is_binary_file(p):
                out.write("[SKIPPED: binary file]\n\n")
                continue

            try:
                data = p.read_bytes()
                text = data.decode("utf-8", errors="replace")
            except Exception as e:
                out.write(f"[SKIPPED: could not read/decode as text: {e}]\n\n")
                continue

            if out_format == "markdown":
                lang = guess_language(p)
                out.write(f"```{lang}\n{text}\n```\n\n")
            else:
                out.write(text)
                if not text.endswith("\n"):
                    out.write("\n")
                out.write("\n")


def main():
    ap = argparse.ArgumentParser(description="Bundle a project folder into one file with structure + contents.")
    ap.add_argument("root", help="Path to the Flask project folder")
    ap.add_argument("-o", "--output", default="project_bundle.md", help="Output file path")
    ap.add_argument("--format", choices=["markdown", "plain"], default="markdown", help="Output format")
    ap.add_argument("--include-hidden", action="store_true", help="Include hidden files/dirs (starting with '.')")
    ap.add_argument("--exclude", action="append", default=[], help="Extra exclude glob (repeatable)")
    ap.add_argument("--no-default-excludes", action="store_true", help="Disable default exclude list")
    ap.add_argument("--max-bytes", type=int, default=1_000_000, help="Skip files larger than this many bytes")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Root folder not found or not a directory: {root}")

    excludes = []
    if not args.no_default_excludes:
        excludes.extend(DEFAULT_EXCLUDES)
    excludes.extend(args.exclude)

    files = collect_files(root, excludes=excludes, include_hidden=args.include_hidden)
    out_path = Path(args.output)

    write_bundle(root, files, out_path=out_path, out_format=args.format, max_bytes=args.max_bytes)

    print(f"Bundled {len(files)} file(s) from: {root}")
    print(f"Output written to: {out_path.resolve()}")


if __name__ == "__main__":
    main()