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
    def __init__(self, project_root: Path) -> None:
        script = files("md2html").joinpath("scripts/mathjax-chtml.mjs")
        package_root = Path(str(files("md2html"))).parent
        roots = (project_root.absolute(), *project_root.absolute().parents, package_root)
        node_modules = next((root / "node_modules" for root in roots if (root / "node_modules/mathjax").is_dir()), project_root / "node_modules")
        self.worker = JsonWorker(
            ["node", Path(str(script)), node_modules], missing="build-time MathJax needs Node.js",
            unavailable="build-time MathJax is unavailable; run npm install in the project directory",
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


_workers: dict[Path, MathJax] = {}
_lock = threading.Lock()


def render_chtml(tex: str, display: bool, project_root: Path) -> Chtml:
    root = project_root.absolute()
    with _lock:
        worker = _workers.get(root)
        if worker is None:
            worker = _workers[root] = MathJax(root)
    return worker.render(tex, display)
