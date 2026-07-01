from __future__ import annotations

import csv
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from .context import BuildContext
from .errors import DirectiveError, IncludeCycleError
from .frontmatter import split_frontmatter

_INCLUDE_RE = re.compile(r"^\s*@include\((?P<path>[^)]+)\)\s*$", re.MULTILINE)
_SRC_RE = re.compile(r"^\s*@src\((?P<args>[^)]*)\)\s*$", re.MULTILINE)
_SRC_REWRITE_RE = re.compile(r"^(?P<prefix>\s*@src\()(?P<args>[^)]*)(?P<suffix>\)\s*)$", re.MULTILINE)


@dataclass
class SrcDirective:
    path: str
    flags: set[str] = field(default_factory=set)
    options: dict[str, str] = field(default_factory=dict)

    @property
    def collapsed(self) -> bool:
        return "collapsed" in self.flags

    @property
    def collapsible(self) -> bool:
        return self.collapsed or "collapsible" in self.flags

    @property
    def expanded_by_default(self) -> bool:
        # User-facing policy:
        #   @src(file)              -> plain expanded code, not collapsible
        #   @src(file, collapsible) -> collapsible and initially expanded
        #   @src(file, collapsed)   -> collapsible and initially collapsed
        return self.collapsible and not self.collapsed


def parse_directive_parts(arg_string: str) -> list[str]:
    try:
        return [part.strip() for part in next(csv.reader([arg_string], skipinitialspace=True)) if part.strip()]
    except Exception:
        return [part.strip() for part in arg_string.split(",") if part.strip()]


def parse_src_directive(arg_string: str) -> SrcDirective:
    parts = parse_directive_parts(arg_string)
    if not parts:
        raise DirectiveError("@src requires a path")
    path = parts[0].strip().strip('"\'')
    flags: set[str] = set()
    options: dict[str, str] = {}
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            options[key.strip().lower()] = value.strip().strip('"\'')
        else:
            flags.add(part.strip().lower())
    return SrcDirective(path=path, flags=flags, options=options)


def iter_include_paths(text: str) -> Iterator[str]:
    for match in _INCLUDE_RE.finditer(text):
        yield match.group("path").strip().strip('"\'')


def iter_src_directives(text: str) -> Iterator[SrcDirective]:
    for match in _SRC_RE.finditer(text):
        yield parse_src_directive(match.group("args"))


def _relative_to_root_source(path: Path, ctx: BuildContext) -> str:
    try:
        return os.path.relpath(path, start=ctx.source_path.parent).replace(os.sep, "/")
    except ValueError:
        return str(path)


def rewrite_src_paths_for_included_markdown(text: str, ctx: BuildContext, *, current_file: Path) -> str:
    """Make @src paths inside included Markdown resolve relative to the include."""

    def repl(match: re.Match[str]) -> str:
        args = match.group("args")
        if "," in args:
            raw_path, rest = args.split(",", 1)
            rest = "," + rest
        else:
            raw_path, rest = args, ""
        quote = '"' if raw_path.strip().startswith('"') else "'" if raw_path.strip().startswith("'") else ""
        clean = raw_path.strip().strip('"\'')
        resolved = ctx.resolve_relative(clean, current_file=current_file)
        rewritten = _relative_to_root_source(resolved, ctx)
        if quote:
            rewritten = f"{quote}{rewritten}{quote}"
        return f"{match.group('prefix')}{rewritten}{rest}{match.group('suffix')}"

    return _SRC_REWRITE_RE.sub(repl, text)


def expand_includes(text: str, ctx: BuildContext, *, current_file: Path | None = None, stack: tuple[Path, ...] = ()) -> str:
    current_file = (current_file or ctx.source_path).resolve()
    if not stack:
        stack = (current_file,)

    def repl(match: re.Match[str]) -> str:
        raw_path = match.group("path").strip().strip('"\'')
        include_path = ctx.resolve_relative(raw_path, current_file=current_file)
        if include_path in stack:
            chain = " -> ".join(str(p) for p in (*stack, include_path))
            raise IncludeCycleError(f"include cycle detected: {chain}")
        if not include_path.exists():
            msg = f"included file not found: {raw_path}"
            if ctx.options.strict:
                raise DirectiveError(msg)
            ctx.warn(msg, path=current_file)
            return f"\n<!-- md2html warning: {msg} -->\n"
        ctx.add_dependency(include_path)
        included = include_path.read_text(encoding="utf-8")
        _metadata, included_body = split_frontmatter(included)
        included_body = rewrite_src_paths_for_included_markdown(included_body, ctx, current_file=include_path)
        return "\n" + expand_includes(included_body, ctx, current_file=include_path, stack=(*stack, include_path.resolve())) + "\n"

    return _INCLUDE_RE.sub(repl, text)
