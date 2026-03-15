"""
Kubernetes driver: namespace, secret, and configmap management.
Uses the kubernetes Python client. Reads kubeconfig from default locations
or from an explicit kubeconfig path.
All operations are idempotent (patch or create).
"""
from __future__ import annotations
import base64
import structlog

logger = structlog.get_logger(__name__)


class KubernetesDriver:
    def __init__(self, kubeconfig_path: str | None = None) -> None:
        from kubernetes import client as k8s_client, config as k8s_config
        if kubeconfig_path:
            k8s_config.load_kube_config(config_file=kubeconfig_path)
        else:
            try:
                k8s_config.load_incluster_config()
            except k8s_config.ConfigException:
                k8s_config.load_kube_config()
        self._core = k8s_client.CoreV1Api()

    def ensure_namespace(self, name: str, labels: dict[str, str] | None = None) -> None:
        from kubernetes.client.exceptions import ApiException
        from kubernetes import client as k8s_client
        ns = k8s_client.V1Namespace(
            metadata=k8s_client.V1ObjectMeta(name=name, labels=labels or {})
        )
        try:
            self._core.create_namespace(ns)
            logger.info("k8s.namespace_created", name=name)
        except ApiException as e:
            if e.status == 409:  # AlreadyExists
                logger.debug("k8s.namespace_exists", name=name)
            else:
                raise

    def ensure_secret(self, namespace: str, name: str, data: dict[str, str], secret_type: str = "Opaque") -> None:
        """Create or replace a k8s Secret. Values in data are plain strings — will be base64-encoded."""
        from kubernetes.client.exceptions import ApiException
        from kubernetes import client as k8s_client
        encoded = {k: base64.b64encode(v.encode()).decode() for k, v in data.items()}
        secret = k8s_client.V1Secret(
            metadata=k8s_client.V1ObjectMeta(name=name, namespace=namespace),
            type=secret_type,
            data=encoded,
        )
        try:
            self._core.create_namespaced_secret(namespace, secret)
            logger.info("k8s.secret_created", name=name, namespace=namespace)
        except ApiException as e:
            if e.status == 409:
                self._core.replace_namespaced_secret(namespace, name, secret)
                logger.info("k8s.secret_updated", name=name, namespace=namespace)
            else:
                raise

    def get_secret(self, namespace: str, name: str) -> dict[str, str] | None:
        """Return decoded secret data or None if not found."""
        from kubernetes.client.exceptions import ApiException
        try:
            secret = self._core.read_namespaced_secret(name, namespace)
            if not secret.data:
                return {}
            return {k: base64.b64decode(v).decode() for k, v in secret.data.items()}
        except ApiException as e:
            if e.status == 404:
                return None
            raise
