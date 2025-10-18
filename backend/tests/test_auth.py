"""
Test Authentication and JWT Utilities

This module tests the authentication, password hashing, and JWT token
functionality for the SaaS Medical Tracker.
"""

from datetime import datetime, timedelta

import pytest
from jose import jwt

from app.core.auth import (
    AuthenticationError,
    TokenError,
    TokenPayload,
    create_access_token,
    create_password_hash,
    create_refresh_token,
    decode_access_token,
    extract_email_from_token,
    extract_user_id_from_token,
    get_authentication_error,
    get_permission_error,
    hash_refresh_token,
    validate_token_format,
    verify_password,
)
from app.core.config import get_settings

settings = get_settings()


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        password = "TestPassword123!"
        hashed = create_password_hash(password)

        # Hash should be different from original
        assert hashed != password

        # Hash should be reasonable length (PBKDF2 is longer than bcrypt)
        assert len(hashed) > 60

        # Hash should start with PBKDF2 identifier
        assert hashed.startswith("$pbkdf2")

    def test_password_verification(self):
        """Test password verification against hash."""
        password = "TestPassword123!"
        hashed = create_password_hash(password)

        # Correct password should verify
        assert verify_password(password, hashed) is True

        # Wrong password should not verify
        assert verify_password("WrongPassword", hashed) is False
        assert verify_password("", hashed) is False
        assert verify_password("testpassword123!", hashed) is False

    def test_password_hash_uniqueness(self):
        """Test that same password generates different hashes (salt)."""
        password = "TestPassword123!"
        hash1 = create_password_hash(password)
        hash2 = create_password_hash(password)

        # Hashes should be different (due to salt)
        assert hash1 != hash2

        # Both should verify the same password
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_password_too_long(self):
        """Test handling of very long passwords."""
        # bcrypt has 72 byte limit
        very_long_password = "a" * 100

        with pytest.raises(AuthenticationError):
            create_password_hash(very_long_password)


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test creating a valid JWT access token."""
        data = {
            "sub": "test@example.com",
            "user_id": "123456"
        }

        token = create_access_token(data)

        # Token should be a string
        assert isinstance(token, str)

        # Token should have 3 parts (header.payload.signature)
        parts = token.split(".")
        assert len(parts) == 3

        # Should be decodable
        payload = decode_access_token(token)
        assert payload["sub"] == data["sub"]
        assert payload["user_id"] == data["user_id"]

    def test_token_expiration(self):
        """Test that tokens have proper expiration."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        payload = decode_access_token(token)

        # Should have expiration
        assert "exp" in payload
        assert "iat" in payload

        # Expiration should be in the future
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        now = datetime.utcnow()

        assert exp_time > now
        assert iat_time <= now

        # Should match configured expiration time
        expected_duration = settings.ACCESS_TOKEN_EXPIRE_SECONDS
        actual_duration = exp_time - iat_time
        assert abs(actual_duration.total_seconds() - expected_duration) < 5  # Allow 5 second tolerance

    def test_custom_expiration(self):
        """Test creating token with custom expiration."""
        data = {"sub": "test@example.com"}
        custom_expires = timedelta(minutes=5)

        token = create_access_token(data, expires_delta=custom_expires)
        payload = decode_access_token(token)

        # Should have custom expiration
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        duration = exp_time - iat_time

        assert abs(duration.total_seconds() - 300) < 5  # 5 minutes ± 5 seconds

    def test_token_claims(self):
        """Test that tokens include proper claims."""
        data = {
            "sub": "test@example.com",
            "user_id": "123456"
        }

        token = create_access_token(data)
        payload = decode_access_token(token)

        # Should include standard claims
        assert payload["sub"] == data["sub"]
        assert payload["user_id"] == data["user_id"]
        assert payload["iss"] == settings.PROJECT_NAME
        assert payload["aud"] == settings.PROJECT_NAME
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_invalid_token(self):
        """Test decoding invalid tokens."""
        with pytest.raises(TokenError):
            decode_access_token("invalid.token.here")

        with pytest.raises(TokenError):
            decode_access_token("not-even-a-token")

        with pytest.raises(TokenError):
            decode_access_token("")

    def test_decode_expired_token(self):
        """Test decoding expired token."""
        data = {"sub": "test@example.com"}
        # Create token that expires immediately
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        with pytest.raises(TokenError, match="expired"):
            decode_access_token(token)

    def test_token_with_wrong_secret(self):
        """Test that tokens signed with wrong secret fail."""
        data = {"sub": "test@example.com"}

        # Create token with wrong secret
        wrong_token = jwt.encode(data, "wrong-secret", algorithm="HS256")

        with pytest.raises(TokenError):
            decode_access_token(wrong_token)


class TestTokenUtilities:
    """Test token utility functions."""

    def test_extract_user_id(self):
        """Test extracting user ID from token."""
        data = {
            "sub": "test@example.com",
            "user_id": "123456"
        }

        token = create_access_token(data)
        user_id = extract_user_id_from_token(token)

        assert user_id == "123456"

    def test_extract_email(self):
        """Test extracting email from token."""
        data = {
            "sub": "test@example.com",
            "user_id": "123456"
        }

        token = create_access_token(data)
        email = extract_email_from_token(token)

        assert email == "test@example.com"

    def test_extract_from_invalid_token(self):
        """Test extracting data from invalid token."""
        assert extract_user_id_from_token("invalid-token") is None
        assert extract_email_from_token("invalid-token") is None

    def test_validate_token_format(self):
        """Test token format validation."""
        # Valid format
        token = validate_token_format("Bearer valid-token-here")
        assert token == "valid-token-here"

        # Invalid formats should raise exception
        with pytest.raises(Exception):
            validate_token_format("Invalid token-here")

        with pytest.raises(Exception):
            validate_token_format("Bearer")

        with pytest.raises(Exception):
            validate_token_format(None)

        with pytest.raises(Exception):
            validate_token_format("")


class TestRefreshTokens:
    """Test refresh token functionality."""

    def test_create_refresh_token(self):
        """Test creating refresh token."""
        user_id = "test-user-123"
        token = create_refresh_token(user_id)

        # Should be a string
        assert isinstance(token, str)

        # Should be reasonably long (32 bytes = 43 chars base64)
        assert len(token) >= 40

    def test_refresh_token_uniqueness(self):
        """Test that refresh tokens are unique."""
        user_id = "test-user-123"
        token1 = create_refresh_token(user_id)
        token2 = create_refresh_token(user_id)

        assert token1 != token2

    def test_hash_refresh_token(self):
        """Test hashing refresh token for storage."""
        token = create_refresh_token("test-user")
        hashed = hash_refresh_token(token)

        # Hash should be hex string
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA256 hex = 64 chars

        # Same token should produce same hash
        hashed2 = hash_refresh_token(token)
        assert hashed == hashed2

        # Different tokens should produce different hashes
        other_token = create_refresh_token("other-user")
        other_hash = hash_refresh_token(other_token)
        assert hashed != other_hash


class TestTokenPayload:
    """Test TokenPayload wrapper class."""

    def test_token_payload_creation(self):
        """Test creating TokenPayload from JWT payload."""
        data = {
            "sub": "test@example.com",
            "user_id": "123456",
            "exp": int(datetime.utcnow().timestamp()) + 3600,
            "iat": int(datetime.utcnow().timestamp()),
            "iss": "test-issuer",
            "aud": "test-audience"
        }

        payload = TokenPayload(data)

        assert payload.sub == "test@example.com"
        assert payload.user_id == "123456"
        assert payload.exp == data["exp"]
        assert payload.iat == data["iat"]
        assert payload.iss == "test-issuer"
        assert payload.aud == "test-audience"

    def test_token_expiration_check(self):
        """Test checking if token is expired."""
        # Non-expired token
        future_exp = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        payload = TokenPayload({"exp": future_exp})
        assert not payload.is_expired()

        # Expired token
        past_exp = int((datetime.utcnow() - timedelta(hours=1)).timestamp())
        payload = TokenPayload({"exp": past_exp})
        assert payload.is_expired()

        # No expiration
        payload = TokenPayload({})
        assert payload.is_expired()  # Should be considered expired

    def test_remaining_time(self):
        """Test getting remaining time before expiration."""
        # Token with 1 hour remaining
        future_exp = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        payload = TokenPayload({"exp": future_exp})
        remaining = payload.get_remaining_time()

        assert remaining is not None
        assert remaining.total_seconds() > 3590  # ~1 hour - 10 seconds
        assert remaining.total_seconds() <= 3600  # ~1 hour

        # Expired token
        past_exp = int((datetime.utcnow() - timedelta(hours=1)).timestamp())
        payload = TokenPayload({"exp": past_exp})
        remaining = payload.get_remaining_time()

        assert remaining is None

        # No expiration
        payload = TokenPayload({})
        remaining = payload.get_remaining_time()

        assert remaining is None


class TestExceptionHelpers:
    """Test authentication exception helpers."""

    def test_authentication_error(self):
        """Test authentication error response."""
        error = get_authentication_error()

        assert error.status_code == 401
        assert "credentials" in error.detail.lower()
        assert "WWW-Authenticate" in error.headers
        assert error.headers["WWW-Authenticate"] == "Bearer"

    def test_permission_error(self):
        """Test permission error response."""
        error = get_permission_error()

        assert error.status_code == 403
        assert "permission" in error.detail.lower()


@pytest.mark.integration
class TestAuthIntegration:
    """Test authentication integration scenarios."""

    def test_full_auth_flow(self):
        """Test complete authentication workflow."""
        # 1. Create user with hashed password
        password = "SecurePassword123!"
        hashed_password = create_password_hash(password)

        # 2. Verify password
        assert verify_password(password, hashed_password)

        # 3. Create access token
        token_data = {
            "sub": "user@example.com",
            "user_id": "user-123"
        }
        access_token = create_access_token(token_data)

        # 4. Validate token
        payload = decode_access_token(access_token)
        assert payload["sub"] == token_data["sub"]
        assert payload["user_id"] == token_data["user_id"]

        # 5. Extract user info from token
        user_id = extract_user_id_from_token(access_token)
        email = extract_email_from_token(access_token)

        assert user_id == token_data["user_id"]
        assert email == token_data["sub"]

        # 6. Create refresh token
        refresh_token = create_refresh_token(user_id)
        refresh_hash = hash_refresh_token(refresh_token)

        assert len(refresh_token) >= 40
        assert len(refresh_hash) == 64


if __name__ == "__main__":
    print("✅ Authentication tests module loaded")
    print("Test classes:")
    print("- TestPasswordHashing: Password hashing and verification")
    print("- TestJWTTokens: JWT token creation and validation")
    print("- TestTokenUtilities: Token utility functions")
    print("- TestRefreshTokens: Refresh token functionality")
    print("- TestTokenPayload: TokenPayload wrapper class")
    print("- TestExceptionHelpers: Authentication exception helpers")
    print("- TestAuthIntegration: Complete authentication workflows")
