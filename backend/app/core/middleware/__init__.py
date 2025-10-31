"""Middleware package exports avoiding circular import.

We need to preserve `from app.core.middleware import setup_middleware, setup_exception_handlers`.
Because this directory shadows the legacy `middleware.py` module name we load that file
under an alternative module name using importlib and re-export its public functions.
We also expose `SessionMiddleware` (session cookie extraction) which is added to the stack
inside the legacy `setup_middleware` implementation (already patched there).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from app.core.session_middleware import SessionMiddleware

_legacy_path = Path(__file__).resolve().parent.parent / "middleware.py"  # parent of package then file
spec = importlib.util.spec_from_file_location("_middleware_stack", str(_legacy_path))
_module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
assert spec and spec.loader
spec.loader.exec_module(_module)  # type: ignore[assignment]

setup_middleware = getattr(_module, "setup_middleware")
setup_exception_handlers = getattr(_module, "setup_exception_handlers")

# Re-export legacy middleware classes so existing imports in tests continue to work.
class AuthenticationMiddleware:  # type: ignore[empty-body]
	...
class CORSMiddleware:  # type: ignore[empty-body]
	...
class RequestIDMiddleware:  # type: ignore[empty-body]
	...
class SecurityHeadersMiddleware:  # type: ignore[empty-body]
	...
class TimingMiddleware:  # type: ignore[empty-body]
	...
class TrustedHostMiddleware:  # type: ignore[empty-body]
	...

_legacy_class_names = [
	"AuthenticationMiddleware",
	"CORSMiddleware",
	"RequestIDMiddleware",
	"SecurityHeadersMiddleware",
	"TimingMiddleware",
	"TrustedHostMiddleware",
]
for _name in _legacy_class_names:
	if hasattr(_module, _name):
		globals()[_name] = getattr(_module, _name)

__all__ = [
	"SessionMiddleware",
	"setup_middleware",
	"setup_exception_handlers",
	"AuthenticationMiddleware",
	"CORSMiddleware",
	"RequestIDMiddleware",
	"SecurityHeadersMiddleware",
	"TimingMiddleware",
	"TrustedHostMiddleware",
]
