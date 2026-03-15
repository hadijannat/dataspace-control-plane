"""
Kubernetes manifest renderer: generates k8s YAML manifests from desired state.
Rendered manifests are applied via kubectl or kubernetes Python client, not via Helm.
"""
from __future__ import annotations
import yaml
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


def render_manifest(template_path: Path, context: dict, output_dir: Path | None = None) -> Path:
    """Render a Jinja2 k8s manifest template."""
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
    import tempfile
    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        undefined=StrictUndefined,
    )
    template = env.get_template(template_path.name)
    rendered = template.render(**context)
    # Validate YAML
    list(yaml.safe_load_all(rendered))  # multi-document ok
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp())
    out = output_dir / template_path.stem
    out.write_text(rendered)
    logger.debug("render.manifest", src=str(template_path), out=str(out))
    return out


def render_namespace_manifest(name: str, labels: dict[str, str] | None = None) -> dict:
    """Return a dict representing a Namespace manifest (no template needed)."""
    return {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {"name": name, "labels": labels or {}},
    }
