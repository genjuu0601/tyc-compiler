"""
Primary static checker entrypoint.

The implementation lives in `static_checker_submission_safe.py` so the same
logic can be reused for local tests and for submission-safe copy/paste.
"""

from .static_checker_submission_safe import StaticChecker

__all__ = ["StaticChecker"]
