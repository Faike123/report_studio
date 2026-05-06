from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader


ROOT = Path(__file__).resolve().parents[2]


def render_html(template_path, context, output_path):
    template_path = Path(template_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    css_path = ROOT / "assets" / "master_report.css"
    master_css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""

    context = dict(context)
    context["master_css"] = master_css

    env = Environment(loader=FileSystemLoader(str(ROOT)))
    template = env.get_template(str(template_path.relative_to(ROOT)))
    html = template.render(**context)

    output_path.write_text(html, encoding="utf-8")
    return output_path
