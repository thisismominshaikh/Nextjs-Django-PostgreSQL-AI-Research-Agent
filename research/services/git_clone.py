"""Clone or resolve a repository to a local checkout path."""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import stat
import subprocess
import time
from pathlib import Path

from django.conf import settings


def _slug(s: str, max_len: int = 80) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", s).strip("_")
    return s[:max_len] or "repo"


def normalize_repo_identifier(repo_url_or_path: str) -> str:
    return repo_url_or_path.strip()


def checkout_path_for(identifier: str) -> Path:
    digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:16]
    slug = _slug(identifier.replace("https://", "").replace("http://", ""))
    return Path(settings.REPO_WORKDIR) / f"{slug}_{digest}"


def _on_rm_error(func, path, exc_info):
    """shutil.rmtree onerror: clear read-only bit (git pack files) and retry."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def _robust_rmtree(path: Path, attempts: int = 6, delay: float = 0.4) -> None:
    """Remove a tree, retrying on Windows file-lock errors (AV / indexer / git)."""
    for i in range(attempts):
        if not path.exists():
            return
        try:
            shutil.rmtree(path, onerror=_on_rm_error)
            return
        except OSError:
            if i == attempts - 1:
                raise
            time.sleep(delay * (2 ** i))


def _robust_replace(src: Path, dst: Path, attempts: int = 6, delay: float = 0.4) -> None:
    """os.replace with retry — Windows can briefly hold handles after git exits."""
    for i in range(attempts):
        try:
            os.replace(src, dst)
            return
        except OSError:
            if i == attempts - 1:
                raise
            time.sleep(delay * (2 ** i))


def ensure_repo_checkout(repo_url_or_path: str) -> tuple[str, Path]:
    """
    Returns (normalized_identifier, absolute_path_to_repo_root).
    For GitHub HTTPS URLs, performs a shallow clone when missing.
    For local paths, validates existence.
    """
    ident = normalize_repo_identifier(repo_url_or_path)
    dest = checkout_path_for(ident)

    if ident.startswith("http://") or ident.startswith("https://"):
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_suffix(dest.suffix + ".tmp")
            _robust_rmtree(tmp)

            # `-c core.longpaths=true` lets git create paths longer than
            # Windows' 260-char MAX_PATH limit.
            cmd = [
                "git",
                "-c", "core.longpaths=true",
                "clone",
                "--depth", "1",
                ident,
                str(tmp),
            ]
            try:
                subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as exc:
                _robust_rmtree(tmp)
                stderr = (exc.stderr or "").strip() or "(no stderr)"
                raise RuntimeError(
                    f"git clone failed (exit {exc.returncode}): {stderr}"
                ) from exc

            # [FIX] Windows often holds a transient lock on freshly-written
            # git pack/index files (AV scan, Search indexer, Defender). The
            # previous code did `shutil.rmtree(dest); tmp.rename(dest)` which
            # raced that lock and crashed with WinError 32. Retry both ops.
            try:
                _robust_rmtree(dest)
                _robust_replace(tmp, dest)
            except OSError as exc:
                _robust_rmtree(tmp)
                raise RuntimeError(
                    f"Repository checkout failed while finalizing destination "
                    f"({exc.__class__.__name__}: {exc}). This is usually "
                    f"antivirus or Windows Search holding a file open in "
                    f"{dest}. Exclude the REPO_WORKDIR from AV/indexing, or "
                    f"set REPO_WORKDIR to a short path like C:\\cf."
                ) from exc

        return ident, dest.resolve()

    p = Path(ident).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Local path does not exist: {p}")
    return str(p), p
