from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from .config import BuildOptions
from .paths import has_private_path_part, resolve_lenient, resolve_markdown_reference


@dataclass
class Diagnostic:
    level: str
    message: str
    path: Path | None = None
    line: int | None = None

    def format(self) -> str:
        loc = ""
        if self.path is not None:
            loc = str(self.path)
            if self.line is not None:
                loc += f":{self.line}"
            loc += ": "
        return f"{self.level.upper()}: {loc}{self.message}"


@dataclass
class BuildContext:
    source_path: Path
    output_path: Path
    options: BuildOptions
    dependencies: set[Path] = field(default_factory=set)
    assets: list[tuple[Path, Path]] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    flags: set[str] = field(default_factory=set)
    dry_run: bool = False

    @property
    def project_root(self) -> Path:
        return self.options.project_root

    def add_dependency(self, path: Path) -> None:
        self.dependencies.add(resolve_lenient(path))

    def use_feature(self, name: str) -> None:
        self.flags.add(name)

    def warn(self, message: str, *, path: Path | None = None, line: int | None = None) -> None:
        self.diagnostics.append(Diagnostic("warning", message, path, line))

    def error(self, message: str, *, path: Path | None = None, line: int | None = None) -> None:
        self.diagnostics.append(Diagnostic("error", message, path, line))

    def resolve_relative(self, raw: str, *, current_file: Path | None = None) -> Path:
        return resolve_markdown_reference(raw, current_file=current_file or self.source_path, project_root=self.project_root)

    def asset_url(self, raw: str, *, current_file: Path | None = None) -> str:
        """Return the URL to use in HTML and queue a local asset copy if possible."""
        if "://" in raw or raw.startswith("#") or raw.startswith("mailto:") or raw.startswith("data:"):
            return raw
        source = self.resolve_relative(raw, current_file=current_file)
        rel = Path(raw)
        if (
            self.options.copy_assets
            and source.exists()
            and source.is_file()
            and not (self.options.output_mode == "html" and has_private_path_part(rel))
        ):
            self.assets.append((source, rel))
        return rel.as_posix()

    def copy_queued_assets(self) -> None:
        if not self.options.copy_assets:
            return
        out_dir = self.output_path.parent
        for src, rel in self.assets:
            if not src.exists() or not src.is_file():
                continue
            dest = out_dir / rel
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                if src.resolve() != dest.resolve():
                    shutil.copy2(src, dest)
            except OSError as exc:
                self.warn(f"could not copy asset {src} -> {dest}: {exc}")
