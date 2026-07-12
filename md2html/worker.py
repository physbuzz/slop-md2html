"""Persistent line-oriented JSON subprocesses."""

from __future__ import annotations

import atexit
import json
from pathlib import Path
import subprocess
import threading
from typing import Any


class WorkerUnavailable(OSError):
    """A selected external renderer cannot be started."""


class JsonWorker:
    def __init__(self, command: list[str | Path], *, missing: str, unavailable: str) -> None:
        try:
            self.process = subprocess.Popen(
                [str(value) for value in command], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, bufsize=1,
            )
        except OSError as error:
            raise WorkerUnavailable(f"{missing}: {error}") from error
        assert self.process.stdout
        ready = self._read()
        if not ready.get("ready"):
            self.close()
            raise WorkerUnavailable(f"{unavailable}: {ready.get('error', 'worker did not start')}")
        self.ready = ready
        self.lock = threading.Lock()
        atexit.register(self.close)

    def request(self, values: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            if self.process.poll() is not None or not self.process.stdin:
                raise WorkerUnavailable("the external renderer stopped")
            self.process.stdin.write(json.dumps(values) + "\n")
            self.process.stdin.flush()
            response = self._read()
        if not response.get("ok"):
            raise ValueError(str(response.get("error", "the external renderer failed")))
        return response

    def _read(self) -> dict[str, Any]:
        assert self.process.stdout
        line = self.process.stdout.readline()
        try:
            return json.loads(line)
        except json.JSONDecodeError as error:
            detail = self.process.stderr.read().strip() if self.process.stderr and self.process.poll() is not None else ""
            raise WorkerUnavailable(detail or "the external renderer returned no response") from error

    def close(self) -> None:
        process = getattr(self, "process", None)
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
