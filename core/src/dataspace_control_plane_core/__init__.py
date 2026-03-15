"""
dataspace-control-plane-core
============================
Installable domain kernel. Import the public surface from each sub-package's api.py.
No framework imports (FastAPI, SQLAlchemy, Temporal, Keycloak SDKs) inside this package.
"""
__version__ = "0.1.0"

from . import api

__all__ = ["__version__", "api"]
