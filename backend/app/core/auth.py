"""
JWT Authentication Utilities

This module provides JWT token generation, validation, and user authentication utilities
for the SaaS Medical Tracker application using python-jose.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import structlog
from fastapi import HTTPException, status
from jose import jwt

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# Use PBKDF2 for now to avoid bcrypt initialization issues in Windows/Python 3.13
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
BCRYPT_AVAILABLE = False
logger.info("Using PBKDF2-SHA256 for password hashing")

# JWT algorithm
ALGORITHM = "HS256"


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class TokenError(Exception):
    """Raised when token operations fail."""
    pass


def create_password_hash(password: str) -> str:
    """
    Create a hashed password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        str: Hashed password
        
    Example:
        >>> hashed = create_password_hash("mypassword123")
        >>> print(len(hashed))  # Should be 60 characters for bcrypt
        60
    """
    try:
        # Check password length in bytes (bcrypt has 72-byte limit)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            raise AuthenticationError("Password is too long. Maximum length is 72 bytes when encoded as UTF-8.")

        # Try direct bcrypt hashing first as fallback
        try:
            hashed = pwd_context.hash(password)
        except ValueError as ve:
            if "password cannot be longer than 72 bytes" in str(ve):
                # If still getting 72-byte error, use first 72 bytes
                truncated_password = password_bytes[:72].decode('utf-8', errors='ignore')
                hashed = pwd_context.hash(truncated_password)
            else:
                raise ve

        logger.debug("Password hashed successfully")
        return hashed
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error("Failed to hash password", error=str(e))
        raise AuthenticationError(f"Failed to hash password: {str(e)}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database
        
    Returns:
        bool: True if password matches, False otherwise
        
    Example:
        >>> hashed = create_password_hash("mypassword123")
        >>> verify_password("mypassword123", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False
    """
    try:
        is_valid = pwd_context.verify(plain_password, hashed_password)
        logger.debug(
            "Password verification completed",
            is_valid=is_valid,
            privacy_filtered=True  # Don't log actual passwords
        )
        return is_valid
    except Exception as e:
        logger.error("Failed to verify password", error=str(e))
        return False


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary of claims to include in the token
        expires_delta: Custom expiration time (defaults to settings)
        
    Returns:
        str: Encoded JWT token
        
    Raises:
        TokenError: If token creation fails
        
    Example:
        >>> token = create_access_token({"sub": "user@example.com", "user_id": "123"})
        >>> print(len(token))  # Should be a long JWT string
    """
    try:
        # Create a copy of the data to avoid mutating the original
        to_encode = data.copy()

        # Set expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)

        # Add standard JWT claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": settings.PROJECT_NAME,
            "aud": settings.PROJECT_NAME,
        })

        # Create the token
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=ALGORITHM
        )

        logger.info(
            "Access token created successfully",
            subject=data.get("sub"),
            expires_at=expire.isoformat(),
            privacy_filtered=True
        )

        return encoded_jwt

    except Exception as e:
        logger.error("Failed to create access token", error=str(e))
        raise TokenError(f"Failed to create access token: {str(e)}")


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Dict[str, Any]: Token payload/claims
        
    Raises:
        TokenError: If token is invalid, expired, or malformed
        
    Example:
        >>> token = create_access_token({"sub": "user@example.com"})
        >>> payload = decode_access_token(token)
        >>> print(payload["sub"])
        user@example.com
    """
    try:
        # Decode the token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=settings.PROJECT_NAME,
            issuer=settings.PROJECT_NAME
        )

        logger.debug(
            "Access token decoded successfully",
            subject=payload.get("sub"),
            privacy_filtered=True
        )

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        raise TokenError("Token has expired")

    except jwt.InvalidTokenError as e:
        logger.warning("Invalid token", error=str(e))
        raise TokenError(f"Invalid token: {str(e)}")

    except Exception as e:
        logger.error("Failed to decode token", error=str(e))
        raise TokenError(f"Failed to decode token: {str(e)}")


def extract_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user ID from a JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        Optional[str]: User ID if found, None otherwise
        
    Example:
        >>> token = create_access_token({"sub": "user@example.com", "user_id": "123"})
        >>> user_id = extract_user_id_from_token(token)
        >>> print(user_id)
        123
    """
    try:
        payload = decode_access_token(token)
        return payload.get("user_id")
    except TokenError:
        return None


def extract_email_from_token(token: str) -> Optional[str]:
    """
    Extract email (subject) from a JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        Optional[str]: Email if found, None otherwise
        
    Example:
        >>> token = create_access_token({"sub": "user@example.com"})
        >>> email = extract_email_from_token(token)
        >>> print(email)
        user@example.com
    """
    try:
        payload = decode_access_token(token)
        return payload.get("sub")
    except TokenError:
        return None


def create_refresh_token(user_id: str) -> str:
    """
    Create a refresh token for long-term authentication.
    
    Args:
        user_id: User identifier
        
    Returns:
        str: Secure random refresh token
        
    Example:
        >>> refresh_token = create_refresh_token("user123")
        >>> print(len(refresh_token))
        64
    """
    try:
        # Generate a secure random token
        token = secrets.token_urlsafe(32)  # 32 bytes = 256 bits

        logger.info(
            "Refresh token created",
            user_id=user_id,
            token_prefix=token[:8] + "...",  # Log only prefix for security
            privacy_filtered=True
        )

        return token

    except Exception as e:
        logger.error("Failed to create refresh token", error=str(e))
        raise TokenError(f"Failed to create refresh token: {str(e)}")


def hash_refresh_token(token: str) -> str:
    """
    Hash a refresh token for secure storage.
    
    Args:
        token: Refresh token to hash
        
    Returns:
        str: Hashed token suitable for database storage
        
    Example:
        >>> token = create_refresh_token("user123")
        >>> hashed = hash_refresh_token(token)
        >>> print(len(hashed))
        64
    """
    return hashlib.sha256(token.encode()).hexdigest()


def get_authentication_error() -> HTTPException:
    """
    Get a standardized HTTP authentication error.
    
    Returns:
        HTTPException: 401 Unauthorized exception
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_permission_error() -> HTTPException:
    """
    Get a standardized HTTP permission error.
    
    Returns:
        HTTPException: 403 Forbidden exception
    """
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions",
    )


# Token validation utilities for FastAPI dependencies
def validate_token_format(authorization: Optional[str]) -> str:
    """
    Validate and extract token from Authorization header.
    
    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")
        
    Returns:
        str: Extracted JWT token
        
    Raises:
        HTTPException: If authorization header is missing or malformed
    """
    if not authorization:
        raise get_authentication_error()

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise get_authentication_error()
        return token
    except ValueError:
        # Split failed - malformed header
        raise get_authentication_error()


class TokenPayload:
    """
    Structured representation of JWT token payload.
    
    Provides type-safe access to token claims.
    """

    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload
        self.sub: Optional[str] = payload.get("sub")
        self.user_id: Optional[str] = payload.get("user_id")
        self.exp: Optional[int] = payload.get("exp")
        self.iat: Optional[int] = payload.get("iat")
        self.iss: Optional[str] = payload.get("iss")
        self.aud: Optional[str] = payload.get("aud")

    def is_expired(self) -> bool:
        """Check if the token is expired."""
        if not self.exp:
            return True
        return datetime.utcnow().timestamp() > self.exp

    def get_remaining_time(self) -> Optional[timedelta]:
        """Get remaining time before token expires."""
        if not self.exp:
            return None

        remaining_seconds = self.exp - datetime.utcnow().timestamp()
        if remaining_seconds <= 0:
            return None

        return timedelta(seconds=remaining_seconds)


# Example usage and testing
if __name__ == "__main__":
    # Test password hashing
    password = "TestPassword123!"
    hashed = create_password_hash(password)
    print(f"Password hashed: {len(hashed)} chars")

    # Test password verification
    is_valid = verify_password(password, hashed)
    is_invalid = verify_password("wrong", hashed)
    print(f"Password verification: valid={is_valid}, invalid={is_invalid}")

    # Test token creation
    token_data = {
        "sub": "test@example.com",
        "user_id": "123e4567-e89b-12d3-a456-426614174000"
    }

    try:
        token = create_access_token(token_data)
        print(f"Token created: {len(token)} chars")

        # Test token decoding
        payload = decode_access_token(token)
        print(f"Token decoded - sub: {payload['sub']}, user_id: {payload['user_id']}")

        # Test token payload wrapper
        token_payload = TokenPayload(payload)
        print(f"Token expires in: {token_payload.get_remaining_time()}")

    except Exception as e:
        print(f"Token test failed: {e}")

    # Test refresh token
    refresh = create_refresh_token("user123")
    refresh_hash = hash_refresh_token(refresh)
    print(f"Refresh token: {len(refresh)} chars, hash: {len(refresh_hash)} chars")

    print("✅ JWT authentication utilities test completed")
