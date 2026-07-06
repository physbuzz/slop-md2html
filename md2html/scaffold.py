from __future__ import annotations

import json

from .rendering import base_css, pygments_css


def example_config_json() -> str:
    data = {
        "input": "notes",
        "output": "html",
        "recursive": True,
        "project_root": ".",
        "output_mode": "html",
        "template_dirs": ["templates"],
        "template": "page.html",
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
    css = pygments_css() + "\n\n" + base_css()
    return (
        '<!DOCTYPE html>\n'
        '<html lang="{{ lang|default(\'en\') }}">\n'
        "<head>\n"
        '  <meta charset="UTF-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "  <title>{{ title }}</title>\n"
        "  {% if use_mathjax %}\n"
        "  <script>\n"
        "    window.MathJax = {\n"
        "      tex: {\n"
        "        inlineMath: [['$', '$']],\n"
        "        displayMath: [['$$', '$$']],\n"
        "        processEscapes: true\n"
        "      }\n"
        "    };\n"
        "  </script>\n"
        '  <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>\n'
        "  {% endif %}\n"
        "  <style>\n"
        "/* Default md2html stylesheet. Edit this block freely. */\n"
        f"{css}"
        "  </style>\n"
        "  <!--\n"
        "  To use md2html's generated CSS instead of this inline stylesheet,\n"
        "  replace the <style> block above with this block:\n\n"
        "  {% raw %}{% if embedded_css %}<style>\n"
        "{{ embedded_css | safe }}\n"
        "  </style>{% endif %}\n"
        '  {% for href in stylesheets %}<link rel="stylesheet" href="{{ href }}">\n'
        "  {% endfor %}{% endraw %}\n"
        "  -->\n"
        "</head>\n"
        "<body>\n"
        '  <main class="container">\n'
        "{{ content | safe }}\n"
        "  </main>\n"
        "</body>\n"
        "</html>\n"
    )
