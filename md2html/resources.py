from __future__ import annotations

import sys
from pathlib import Path


def package_resource_path(relative_path: str | Path) -> Path:
    """Resolve bundled md2html resources in source and executable builds."""
    rel = Path(relative_path)
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / "md2html" / rel
    return Path(__file__).resolve().parent / rel
