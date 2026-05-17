"""Filesystem-backed code exploration tools (list/read/search/summary)."""
# [AI] Standard imports for filesystem traversal and pattern matching.
from __future__ import annotations

import fnmatch
import os
import re
from pathlib import Path

from django.conf import settings

# [MOMIN] Directory blacklist: VCS metadata, virtualenvs, build outputs, IDE state.
# [MOMIN] These directories are huge and noisy, and the agent gains nothing by
# [MOMIN] reading them. Skipping them here (instead of in the agent prompt) makes
# [MOMIN] the safety property structural, not advisory.
SKIP_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    "dist",
    "build",
    ".idea",
    ".vscode",
}

# [MOMIN] Whitelist of file extensions we treat as "probably text". Whitelisting
# [MOMIN] (rather than blacklisting binaries) prevents accidentally pumping
# [MOMIN] binary blobs through `read_file` if a new exotic format shows up.
TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".rst",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".sql",
    ".sh",
    ".ps1",
    ".xml",
    ".gradle",
    ".properties",
    ".swift",
    ".vue",
    ".scss",
    ".sass",
    ".dockerfile",
    "",
}


def _safe_join(root: Path, rel: str) -> Path:
    # [MOMIN] Path-traversal guard. Resolving both sides and asserting that the
    # [MOMIN] candidate is `root` itself or a descendant prevents the model from
    # [MOMIN] escaping the checkout via "../" tricks or symlink chains. This is
    # [MOMIN] the single most important security check in the file-tools layer.
    rel = (rel or ".").replace("\\", "/").lstrip("/")
    candidate = (root / rel).resolve()
    root_resolved = root.resolve()
    if root_resolved == candidate or root_resolved in candidate.parents:
        return candidate
    raise ValueError("Path escapes repository root")


def list_files(root: Path, path: str = ".", max_entries: int = 400) -> dict:
    """List files and directories under path (relative to repo root)."""
    # [AI] Resolve the requested directory inside the repo root.
    base = _safe_join(root, path)
    if not base.exists():
        return {"error": f"path not found: {path}"}
    out: list[dict] = []

    # [MOMIN] We *intentionally* don't recurse — `walk()` here only iterates the
    # [MOMIN] requested directory level. Recursive listing would explode the
    # [MOMIN] response on large repos and the agent can drill down on demand.
    def walk(cur: Path, prefix: str) -> None:
        nonlocal out
        if len(out) >= max_entries:
            return
        try:
            # [AI] Sort: directories first, then alphabetic case-insensitive.
            entries = sorted(cur.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError as e:
            out.append({"path": prefix or ".", "type": "error", "detail": str(e)})
            return
        for child in entries:
            if len(out) >= max_entries:
                break
            rel = os.path.relpath(child, root).replace("\\", "/")
            if child.is_dir():
                if child.name in SKIP_DIR_NAMES:
                    continue
                out.append({"path": rel, "type": "dir"})
            else:
                try:
                    size = child.stat().st_size
                except OSError:
                    size = None
                out.append({"path": rel, "type": "file", "size": size})

    if base.is_file():
        # [AI] Calling list_files on a file returns a single-entry result.
        rel = os.path.relpath(base, root).replace("\\", "/")
        out.append({"path": rel, "type": "file"})
        return {"root": str(root), "path": path, "entries": out, "truncated": False}

    walk(base, os.path.relpath(base, root).replace("\\", "/") if base != root else ".")
    truncated = len(out) >= max_entries
    return {"root": str(root), "path": path, "entries": out, "truncated": truncated}


def read_file(root: Path, path: str, start_line: int | None = None, end_line: int | None = None) -> dict:
    """Read a text file with optional 1-based inclusive line range."""
    # [AI] Resolve and validate the requested file path.
    fp = _safe_join(root, path)
    if not fp.is_file():
        return {"error": f"not a file: {path}"}
    # [MOMIN] All bytes are read up-front then decoded with UTF-8 + replacement.
    # [MOMIN] We accept that suboptimal vs streamed reads — repo files are small
    # [MOMIN] and the simpler code path avoids partial-decode bugs.
    max_chars = settings.AGENT_READ_FILE_MAX_CHARS
    raw = fp.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")

    # [AI] Compute the inclusive line slice based on the optional bounds.
    lines = text.splitlines()
    total = len(lines)
    s = 1 if start_line is None else max(1, start_line)
    e = total if end_line is None else min(total, end_line)
    if s > total:
        slice_lines: list[str] = []
    else:
        slice_lines = lines[s - 1 : e]

    # [MOMIN] We prefix each output line with `<lineno>|` so the model can produce
    # [MOMIN] precise citations (file + line number) without separately tracking
    # [MOMIN] the offset. The final character cap is a hard upper bound on cost.
    numbered = "\n".join(f"{i + s}|{line}" for i, line in enumerate(slice_lines))
    if len(numbered) > max_chars:
        numbered = numbered[:max_chars] + "\n...[truncated]"

    return {
        "path": path,
        "start_line": s,
        "end_line": e if end_line is not None else total,
        "total_lines": total,
        "content": numbered,
    }


def _is_probably_text(path: Path) -> bool:
    # [AI] Whitelist by extension, with a small set of well-known extensionless files.
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    name = path.name.lower()
    if name in {"dockerfile", "makefile", "license", "readme"}:
        return True
    return False


def _glob_matches(rel: str, pattern: str) -> bool:
    # [AI] Tolerant glob matcher: handles "**/" prefix the way users expect.
    if pattern in ("", "**/*"):
        return True
    if fnmatch.fnmatch(rel, pattern):
        return True
    if pattern.startswith("**/"):
        alt = pattern[3:]
        return fnmatch.fnmatch(rel, alt) or fnmatch.fnmatch(os.path.basename(rel), alt)
    return False


def search_code(root: Path, query: str, glob_pattern: str = "**/*") -> dict:
    """Simple substring search across text-like files under root."""
    # [MOMIN] We deliberately ship a substring scan instead of regex/embeddings:
    # [MOMIN] zero new dependencies, deterministic behavior, and "good enough"
    # [MOMIN] for assessment-scale repos. The directory skip-list and a hard
    # [MOMIN] match cap keep worst-case runtime predictable.
    if not query.strip():
        return {"error": "empty query"}
    q = query
    max_matches = settings.AGENT_SEARCH_MAX_MATCHES
    matches: list[dict] = []

    # [MOMIN] Mutating `dirnames[:]` in-place is the canonical os.walk idiom for
    # [MOMIN] pruning whole subtrees — much cheaper than filtering after the fact.
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        for name in filenames:
            if len(matches) >= max_matches:
                break
            fp = Path(dirpath) / name
            rel = str(fp.relative_to(root)).replace("\\", "/")
            if not _glob_matches(rel, glob_pattern):
                continue
            if not _is_probably_text(fp):
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), start=1):
                if q in line:
                    # [AI] Trim the snippet so individual matches stay small.
                    matches.append(
                        {
                            "path": rel,
                            "line": i,
                            "snippet": line.strip()[:500],
                        }
                    )
                    if len(matches) >= max_matches:
                        break
    return {
        "query": query,
        "match_count": len(matches),
        "truncated": len(matches) >= max_matches,
        "matches": matches,
    }


def get_file_summary(root: Path, path: str, preview_lines: int = 40) -> dict:
    """Heuristic summary: size, line count, preview, top-level defs."""
    # [AI] Resolve and validate the file path.
    fp = _safe_join(root, path)
    if not fp.is_file():
        return {"error": f"not a file: {path}"}
    try:
        text = fp.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return {"error": str(e)}
    lines = text.splitlines()
    total = len(lines)
    # [AI] Take the first N lines as a preview block, line-numbered.
    preview = "\n".join(f"{i+1}|{lines[i]}" for i in range(min(preview_lines, total)))

    # [MOMIN] Cheap "structure hint" extraction: grep for `def`/`class`/`async def`
    # [MOMIN] in the first 2000 lines. This is Python-biased on purpose — it's
    # [MOMIN] fast, dependency-free, and gives the model a usable outline. Real
    # [MOMIN] AST/tree-sitter parsing would be the next iteration.
    defs: list[str] = []
    for i, line in enumerate(lines[:2000], start=1):
        if re.match(r"^(def |class |async def )", line):
            defs.append(f"L{i}: {line.strip()[:200]}")

    return {
        "path": path,
        "bytes": fp.stat().st_size,
        "total_lines": total,
        "preview": preview,
        "structure_hints": defs[:80],
    }
