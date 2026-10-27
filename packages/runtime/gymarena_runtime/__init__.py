"""Shared operational endpoints, without shared domain data or business rules."""
from .app import create_app

__all__ = ["create_app"]
