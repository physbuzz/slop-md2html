"""One persistent build-time MathJax process per Python process."""

from __future__ import annotations

import atexit
from dataclasses import dataclass
from importlib.resources import files
import json
from pathlib import Path
import re
import subprocess
import threading


@dataclass(frozen=True)
class Chtml:
    html: str
    css: str
    font_dir: Path


class MathJax:
    def __init__(self) -> None:
        script = files("md2html2").joinpath("scripts/mathjax-chtml.mjs")
        try:
            self.process = subprocess.Popen(
                ["node", str(script)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, bufsize=1,
            )
        except OSError as error:
            raise RuntimeError(f"build-time MathJax needs Node.js: {error}") from error
        assert self.process.stdout
        line = self.process.stdout.readline()
        try:
            ready = json.loads(line)
        except json.JSONDecodeError:
            ready = {"ready": False, "error": self._errors() or "worker did not start"}
        if not ready.get("ready"):
            self.close()
            raise RuntimeError(
                "build-time MathJax is unavailable; run npm install in the md2html2 package: "
                + str(ready.get("error", "unknown error"))
            )
        self.css = re.sub(r"^\s*<style\b[^>]*>|</style>\s*$", "", str(ready["css"]), flags=re.I)
        self.font_dir = Path(str(ready["fontDir"]))
        self.lock = threading.Lock()
        atexit.register(self.close)

    def render(self, tex: str, display: bool) -> Chtml:
        with self.lock:
            if self.process.poll() is not None or not self.process.stdin or not self.process.stdout:
                raise RuntimeError("the build-time MathJax process stopped")
            self.process.stdin.write(json.dumps({"tex": tex, "display": display}) + "\n")
            self.process.stdin.flush()
            response = json.loads(self.process.stdout.readline())
        if not response.get("ok"):
            raise ValueError(response.get("error", "MathJax could not render the expression"))
        self.css = re.sub(r"^\s*<style\b[^>]*>|</style>\s*$", "", str(response["css"]), flags=re.I)
        return Chtml(str(response["html"]), self.css, self.font_dir)

    def _errors(self) -> str:
        if self.process.stderr and self.process.poll() is not None:
            return self.process.stderr.read().strip()
        return ""

    def close(self) -> None:
        process = getattr(self, "process", None)
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()


_worker: MathJax | None = None
_lock = threading.Lock()


def render_chtml(tex: str, display: bool) -> Chtml:
    global _worker
    with _lock:
        if _worker is None:
            _worker = MathJax()
    return _worker.render(tex, display)
