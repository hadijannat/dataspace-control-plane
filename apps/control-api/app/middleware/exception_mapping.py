"""Re-export install_exception_handlers for middleware package consistency."""
from app.api.errors import install_exception_handlers

__all__ = ["install_exception_handlers"]
