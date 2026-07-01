from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path


def resolve_lenient(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def has_private_path_part(path: Path) -> bool:
    return any(part.startswith("_") for part in path.parts)


def dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for path in paths:
        resolved = resolve_lenient(path)
        if resolved not in seen:
            seen.add(resolved)
            out.append(resolved)
    return out


def is_ignored(path: Path, ignored_roots: Iterable[Path]) -> bool:
    resolved = resolve_lenient(path)
    return any(is_relative_to(resolved, resolve_lenient(root)) for root in ignored_roots)


def source_output_path(src: Path, suffix: str) -> Path:
    if suffix.startswith("."):
        return src.with_suffix(suffix)
    return src.with_name(src.name + suffix)


def resolve_markdown_reference(raw: str, *, current_file: Path, project_root: Path) -> Path:
    raw_path = Path(raw).expanduser()
    if raw_path.is_absolute():
        return resolve_lenient(raw_path)
    candidate = resolve_lenient(current_file.parent / raw_path)
    if candidate.exists():
        return candidate
    return resolve_lenient(project_root / raw_path)
