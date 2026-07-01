from __future__ import annotations

import os
import re
from pathlib import Path

from .context import BuildContext
from .errors import IncludeCycleError, DirectiveError
from .frontmatter import split_frontmatter

_INCLUDE_RE = re.compile(r"^\s*@include\((?P<path>[^)]+)\)\s*$", re.MULTILINE)
_SRC_RE = re.compile(r"^(?P<prefix>\s*@src\()(?P<args>[^)]*)(?P<suffix>\)\s*)$", re.MULTILINE)


def _relative_to_root_source(path: Path, ctx: BuildContext) -> str:
    try:
        return os.path.relpath(path, start=ctx.source_path.parent).replace(os.sep, "/")
    except ValueError:
        return str(path)


def _rewrite_src_paths_for_included_body(text: str, ctx: BuildContext, *, current_file: Path) -> str:
    """Make @src paths inside included Markdown resolve as they did locally.

    Includes are expanded before code directives are processed. Without this
    rewrite, an included file's ``@src(../code/main.cpp)`` would later be
    resolved relative to the root page instead of relative to the included file.
    """

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

    return _SRC_RE.sub(repl, text)


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
        included_body = _rewrite_src_paths_for_included_body(included_body, ctx, current_file=include_path)
        return "\n" + expand_includes(included_body, ctx, current_file=include_path, stack=(*stack, include_path.resolve())) + "\n"

    return _INCLUDE_RE.sub(repl, text)
