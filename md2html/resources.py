from __future__ import annotations

from importlib import metadata
import sys
from pathlib import Path


def package_resource_path(relative_path: str | Path) -> Path:
    """Resolve bundled md2html resources in source and executable builds."""
    rel = Path(relative_path)
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / "md2html" / rel
    return Path(__file__).resolve().parent / rel


def read_project_readme() -> str:
    for path in (package_resource_path("../readme.md"), package_resource_path("readme.md")):
        if path.exists():
            return path.read_text(encoding="utf-8")
    try:
        description = metadata.metadata("md2html").get_payload()
    except metadata.PackageNotFoundError:
        description = ""
    if isinstance(description, str) and description.strip():
        return description
    raise FileNotFoundError("readme.md")
