"""
Values file renderer: generates Helm values YAML from desired state models.
Uses Jinja2 for templating. Output files are written to a temp dir and passed to HelmDriver.
Secrets are references (vault paths), not raw values.
"""
from __future__ import annotations
import tempfile
import yaml
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


def render_values_file(template_path: Path, context: dict, output_dir: Path | None = None) -> Path:
    """
    Render a Jinja2 YAML template into a values file.
    Returns path to the rendered file.
    context must NOT contain raw secrets — only vault reference paths.
    """
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        undefined=StrictUndefined,
    )
    template = env.get_template(template_path.name)
    rendered = template.render(**context)
    # Validate it's parseable YAML before writing
    yaml.safe_load(rendered)
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp())
    output_path = output_dir / f"{template_path.stem}.rendered.yaml"
    output_path.write_text(rendered)
    logger.debug("render.values_file", src=str(template_path), out=str(output_path))
    return output_path


def render_all_values(templates_dir: Path, context: dict, output_dir: Path | None = None) -> list[Path]:
    """Render all *.values.yaml.j2 templates in a directory."""
    templates_dir = Path(templates_dir)
    rendered: list[Path] = []
    for template_path in sorted(templates_dir.glob("*.values.yaml.j2")):
        rendered.append(render_values_file(template_path, context, output_dir))
    return rendered
