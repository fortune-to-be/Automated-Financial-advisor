"""Compatibility shim for AuthService import path used by some tests.

Provides a small wrapper exposing `generate_tokens` for tests that expect
that method name while delegating to the primary AuthService implementation
in `app.services`.
"""
from app.services import AuthService as _PrimaryAuthService


class AuthService:
	"""Thin wrapper exposing the legacy `generate_tokens` API expected by tests."""

	def generate_tokens(self, user_id: int, additional_claims=None):
		return _PrimaryAuthService.create_tokens(user_id, additional_claims=additional_claims)


__all__ = ["AuthService"]
