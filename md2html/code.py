from __future__ import annotations

import html
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .context import BuildContext
from .directives import SrcDirective, parse_directive_parts, parse_src_directive
from .errors import DirectiveError
from .paths import source_output_path
from .rendering import highlight_code, language_for_path


def _output_path_for_source(src: Path, ctx: BuildContext) -> Path:
    return source_output_path(src, ctx.options.code.output_suffix)


def _command_from_config(src: Path, ctx: BuildContext) -> list[str] | None:
    commands = ctx.options.code.commands or {}
    key_candidates = [src.suffix.lstrip("."), src.suffix, language_for_path(src)]
    raw = None
    for key in key_candidates:
        if key in commands:
            raw = commands[key]
            break
    if raw is None:
        return None
    if isinstance(raw, str):
        return [part.format(src=str(src), stem=str(src.with_suffix(""))) for part in shlex.split(raw)]
    if isinstance(raw, list):
        return [str(part).format(src=str(src), stem=str(src.with_suffix(""))) for part in raw]
    raise DirectiveError(f"invalid command for {src.suffix}: expected string or list")


def _default_command(src: Path) -> list[str] | None:
    suffix = src.suffix.lower()
    if suffix == ".py":
        if getattr(sys, "frozen", False):
            python = shutil.which("python3") or shutil.which("python")
            return [python or "python3", str(src)]
        return [sys.executable, str(src)]
    if suffix in {".sh", ".bash"}:
        return ["bash", str(src)]
    if suffix in {".js", ".mjs"}:
        return ["node", str(src)]
    if suffix in {".rkt", ".scm"}:
        return ["racket", str(src)]
    return None


def _run_compiled(src: Path, ctx: BuildContext) -> subprocess.CompletedProcess[str]:
    suffix = src.suffix.lower()
    compiler = "g++" if suffix in {".cpp", ".cc", ".cxx"} else "gcc"
    if shutil.which(compiler) is None:
        raise FileNotFoundError(compiler)
    with tempfile.TemporaryDirectory(prefix="md2html-build-") as tmp:
        exe = Path(tmp) / (src.stem + (".exe" if os.name == "nt" else ""))
        compile_cmd = [compiler, str(src), "-std=c++17" if compiler == "g++" else "-std=c11", "-O2", "-o", str(exe)]
        subprocess.run(
            compile_cmd,
            cwd=src.parent,
            text=True,
            capture_output=True,
            timeout=ctx.options.code.timeout,
            check=True,
        )
        return subprocess.run(
            [str(exe)],
            cwd=src.parent,
            text=True,
            capture_output=True,
            timeout=ctx.options.code.timeout,
            check=False,
        )


def execute_source(src: Path, ctx: BuildContext) -> str | None:
    try:
        if src.suffix.lower() in {".cpp", ".cc", ".cxx", ".c"} and _command_from_config(src, ctx) is None:
            result = _run_compiled(src, ctx)
        else:
            cmd = _command_from_config(src, ctx) or _default_command(src)
            if not cmd:
                ctx.warn(f"no execution command configured for {src.suffix}; source embedded without output", path=src)
                return None
            if shutil.which(cmd[0]) is None and not Path(cmd[0]).exists():
                ctx.warn(f"command not found: {cmd[0]}; source embedded without output", path=src)
                return None
            result = subprocess.run(
                cmd,
                cwd=src.parent,
                text=True,
                capture_output=True,
                timeout=ctx.options.code.timeout,
                check=False,
            )
    except subprocess.TimeoutExpired:
        ctx.warn(f"execution timed out after {ctx.options.code.timeout:g}s", path=src)
        return None
    except subprocess.CalledProcessError as exc:
        output = (exc.stdout or "") + (exc.stderr or "")
        ctx.warn(f"command failed with exit code {exc.returncode}", path=src)
        return output
    except FileNotFoundError as exc:
        ctx.warn(f"command not found: {exc.filename}", path=src)
        return None

    output = result.stdout or ""
    if result.stderr:
        output += ("\n" if output else "") + result.stderr
    if result.returncode != 0:
        ctx.warn(f"command exited with status {result.returncode}", path=src)
    out_file = _output_path_for_source(src, ctx)
    try:
        out_file.write_text(output, encoding="utf-8")
        ctx.add_dependency(out_file)
    except OSError as exc:
        ctx.warn(f"could not write output file {out_file}: {exc}", path=src)
    return output


def _output_is_stale(src: Path, out_file: Path, ctx: BuildContext) -> bool:
    if ctx.options.force_rebuild or not out_file.exists():
        return True
    try:
        return src.stat().st_mtime > out_file.stat().st_mtime
    except OSError:
        return True


def _read_or_execute_output(src: Path, ctx: BuildContext) -> str | None:
    out_file = _output_path_for_source(src, ctx)
    if ctx.options.execute and not ctx.dry_run and _output_is_stale(src, out_file, ctx):
        return execute_source(src, ctx)
    if out_file.exists():
        ctx.add_dependency(out_file)
        return out_file.read_text(encoding="utf-8")
    if ctx.options.execute:
        # In dry-run/watch planning, record the future generated output without
        # executing the source or touching the filesystem.
        ctx.add_dependency(out_file)
    return None


def _render_output(output: str | None) -> str:
    if output is None:
        return ""
    return (
        '<div class="code-output">\n'
        '<span>Output:</span>\n'
        f'<pre>{html.escape(output)}</pre>\n'
        '</div>\n'
    )


def render_source_embed(src: Path, ctx: BuildContext, directive: SrcDirective) -> str:
    if not src.exists():
        message = f"source file not found: {directive.path}"
        if ctx.options.strict:
            raise DirectiveError(message)
        ctx.warn(message, path=ctx.source_path)
        return f'<div class="md2html-warning">{html.escape(message)}</div>'

    ctx.add_dependency(src)
    code = src.read_text(encoding="utf-8")
    lang = directive.options.get("lang") or language_for_path(src)
    highlighted = highlight_code(code, lang, filename=str(src))
    output = _read_or_execute_output(src, ctx)
    href = ctx.asset_url(directive.path, current_file=ctx.source_path)
    label = directive.options.get("caption") or directive.path

    header = f'<div class="code-header"><a href="{html.escape(href, quote=True)}">{html.escape(label)}</a></div>\n'
    if directive.collapsible:
        open_attr = " open" if directive.expanded_by_default else ""
        code_html = (
            '<div class="code-box">\n'
            f'<details class="collapsible-code"{open_attr}>\n'
            f'<summary class="code-summary"><a href="{html.escape(href, quote=True)}">{html.escape(label)}</a> '
            '<span class="expand-hint">(click to expand)</span></summary>\n'
            f'{highlighted}\n'
            '</details>\n'
            f'{_render_output(output)}'
            '</div>\n'
        )
        return code_html
    return '<div class="code-box">\n' + header + highlighted + _render_output(output) + '</div>\n'


def render_inline_source(code: str, lang: str, flags: set[str]) -> str:
    highlighted = highlight_code(code, lang)
    extra = ""
    if "godbolt" in flags:
        extra = '<div class="code-header"><a href="https://godbolt.org/" target="_blank" rel="noopener">Open in Compiler Explorer</a></div>\n'
    return '<div class="code-box inline-source">\n' + extra + highlighted + '</div>\n'


def expand_code_directives(text: str, ctx: BuildContext) -> str:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("@src(") and stripped.endswith(")"):
            arg_string = stripped[len("@src(") : -1]
            directive = parse_src_directive(arg_string)
            src = ctx.resolve_relative(directive.path, current_file=ctx.source_path)
            out.append(render_source_embed(src, ctx, directive))
            i += 1
            continue
        if stripped.startswith("@src-begin(") and stripped.endswith(")"):
            arg_string = stripped[len("@src-begin(") : -1]
            parts = parse_directive_parts(arg_string)
            lang = parts[0] if parts else "text"
            flags = {part.lower() for part in parts[1:]}
            block: list[str] = []
            i += 1
            while i < len(lines) and lines[i].strip() != "@src-end":
                block.append(lines[i])
                i += 1
            if i < len(lines) and lines[i].strip() == "@src-end":
                i += 1
            out.append(render_inline_source("\n".join(block) + "\n", lang, flags))
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")
