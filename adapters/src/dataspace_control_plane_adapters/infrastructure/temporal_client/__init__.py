"""Temporal client infrastructure adapter.

Thin async wrapper around temporalio.client. Implements procedure_runtime/ports.py
WorkflowGatewayPort. Only apps/ and Activity functions should import this package.
Never import from workflow code in procedures/.
"""
from __future__ import annotations
