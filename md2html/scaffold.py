from __future__ import annotations

import json

from .config import BuildOptions
from .rendering import ALL_FEATURES, bundled_template_text, embedded_css_for_template


def example_config_json() -> str:
    data = {
        "input": "notes",
        "output": "html",
        "recursive": True,
        "project_root": ".",
        "output_mode": "html",
        "template_dirs": ["templates"],
        "template": "page.html",
        "css": None,
        "feature_css": True,
        "copy_assets": True,
        "embed_assets": True,
        "execute": False,
        "no_overwrite": False,
        "force_rebuild": False,
        "strict": False,
        "verbose": False,
        "math": {
            "backend": "mathjax",
        },
        "images": {
            "class": "note-image",
            "width": "70%",
        },
        "code": {
            "commands": {
                "wl": "wolframscript -file {src}",
            },
            "timeout": 15,
            "output_suffix": ".out",
            "highlight_style": "default",
            "highlight_dark_style": "github-dark",
        },
        "jekyll": {
            "math": "passthrough",
            "layout": "post",
            "stylesheet": "assets/css/md2html.css",
            "highlight_fences": False,
            "frontmatter": {
                "render_with_liquid": False,
            },
        },
    }
    return json.dumps(data, indent=2) + "\n"


def example_layout_html() -> str:
    template = bundled_template_text("page.html")
    css = embedded_css_for_template("page.html", BuildOptions(), features=ALL_FEATURES)
    dynamic_block = (
        "  {% if embedded_css %}<style>\n"
        "{{ embedded_css | safe }}\n"
        "  </style>{% endif %}"
    )
    inline_block = (
        "  <style>\n"
        "/* Default md2html page stylesheet. Edit this block freely. */\n"
        f"{css}"
        "  </style>\n"
        "  <!--\n"
        "  To use md2html's selected CSS instead of this inline stylesheet,\n"
        "  replace the <style> block above with this block:\n\n"
        "  {% raw %}{% if embedded_css %}<style>\n"
        "{{ embedded_css | safe }}\n"
        "  </style>{% endif %}{% endraw %}\n"
        "  -->"
    )
    return template.replace(dynamic_block, inline_block)
