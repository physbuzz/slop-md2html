"""One persistent build-time MathJax process per Python process."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
import re
import threading

from .worker import JsonWorker


@dataclass(frozen=True)
class Chtml:
    html: str
    css: str
    font_dir: Path


class MathJax:
    def __init__(self) -> None:
        script = files("md2html2").joinpath("scripts/mathjax-chtml.mjs")
        self.worker = JsonWorker(
            ["node", Path(str(script))], missing="build-time MathJax needs Node.js",
            unavailable="build-time MathJax is unavailable; run npm install in the md2html2 package",
        )
        ready = self.worker.ready
        self.css = re.sub(r"^\s*<style\b[^>]*>|</style>\s*$", "", str(ready["css"]), flags=re.I)
        self.font_dir = Path(str(ready["fontDir"]))

    def render(self, tex: str, display: bool) -> Chtml:
        response = self.worker.request({"tex": tex, "display": display})
        self.css = re.sub(r"^\s*<style\b[^>]*>|</style>\s*$", "", str(response["css"]), flags=re.I)
        return Chtml(str(response["html"]), self.css, self.font_dir)

    def close(self) -> None:
        self.worker.close()


_worker: MathJax | None = None
_lock = threading.Lock()


def render_chtml(tex: str, display: bool) -> Chtml:
    global _worker
    with _lock:
        if _worker is None:
            _worker = MathJax()
    return _worker.render(tex, display)
