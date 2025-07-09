from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
import secrets
import string
from uuid import UUID

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


class TokenData(BaseModel):
    """Token payload data model."""
    email: Optional[EmailStr] = None
    user_id: Optional[str] = None
    permissions: list[str] = []
    role: Optional[str] = None
    token_type: str = "access"


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to verify against
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def validate_password(password: str) -> bool:
    """
    Validate password meets security requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        bool: True if password meets requirements
        
    Raises:
        ValueError: If password doesn't meet requirements
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
    
    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one digit")
    
    if not any(char.isupper() for char in password):
        raise ValueError("Password must contain at least one uppercase letter")
    
    if not any(char.islower() for char in password):
        raise ValueError("Password must contain at least one lowercase letter")
    
    return True


def generate_password(length: int = 12) -> str:
    """
    Generate a secure random password.
    
    Args:
        length: Length of password to generate
        
    Returns:
        str: Generated password
    """
    # Ensure minimum length
    length = max(length, settings.PASSWORD_MIN_LENGTH)
    
    # Character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%^&*"
    
    # Ensure at least one character from each set
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special),
    ]
    
    # Fill the rest of the password
    all_characters = lowercase + uppercase + digits + special
    for _ in range(length - 4):
        password.append(secrets.choice(all_characters))
    
    # Shuffle the password
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    
    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add token metadata
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    # Encode token
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Data to encode in the token
        
    Returns:
        str: Encoded JWT refresh token
    """
    to_encode = data.copy()
    
    # Set expiration
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Add token metadata
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": secrets.token_urlsafe(32)  # Unique token ID for revocation
    })
    
    # Encode token
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        expected_type: Expected token type (access or refresh)
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Verify token type
        token_type = payload.get("type")
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}, got {token_type}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def decode_access_token(token: str) -> TokenData:
    """
    Decode an access token and return token data.
    
    Args:
        token: JWT access token
        
    Returns:
        TokenData: Decoded token data
        
    Raises:
        HTTPException: If token is invalid
    """
    payload = verify_token(token, expected_type="access")
    
    # Extract token data
    email = payload.get("sub")
    user_id = payload.get("user_id")
    permissions = payload.get("permissions", [])
    role = payload.get("role")
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return TokenData(
        email=email,
        user_id=user_id,
        permissions=permissions,
        role=role,
        token_type="access"
    )


async def get_current_token(token: str = Depends(oauth2_scheme)) -> str:
    """
    Dependency to get the current token.
    
    Args:
        token: Bearer token from request header
        
    Returns:
        str: The token
    """
    return token


async def get_current_user_data(token: str = Depends(get_current_token)) -> TokenData:
    """
    Dependency to get current user data from token.
    
    Args:
        token: JWT token
        
    Returns:
        TokenData: Current user's token data
    """
    return decode_access_token(token)


def create_api_key() -> str:
    """
    Create a secure API key.
    
    Returns:
        str: Generated API key
    """
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for storage.
    
    Args:
        api_key: Plain API key
        
    Returns:
        str: Hashed API key
    """
    # Use the same context as passwords but could use a different one
    return pwd_context.hash(api_key)


def verify_api_key(plain_api_key: str, hashed_api_key: str) -> bool:
    """
    Verify an API key against its hash.
    
    Args:
        plain_api_key: Plain API key
        hashed_api_key: Hashed API key
        
    Returns:
        bool: True if API key is valid
    """
    return pwd_context.verify(plain_api_key, hashed_api_key)


def create_password_reset_token(email: str) -> str:
    """
    Create a password reset token.
    
    Args:
        email: User's email address
        
    Returns:
        str: Password reset token
    """
    data = {
        "sub": email,
        "type": "password_reset"
    }
    
    # Password reset tokens expire in 1 hour
    expires_delta = timedelta(hours=1)
    
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify a password reset token and return the email.
    
    Args:
        token: Password reset token
        
    Returns:
        Optional[str]: Email address if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_type = payload.get("type")
        
        if token_type != "password_reset":
            return None
            
        email = payload.get("sub")
        return email
        
    except JWTError:
        return None


def create_email_verification_token(email: str) -> str:
    """
    Create an email verification token.
    
    Args:
        email: Email address to verify
        
    Returns:
        str: Email verification token
    """
    data = {
        "sub": email,
        "type": "email_verification"
    }
    
    # Email verification tokens expire in 24 hours
    expires_delta = timedelta(hours=24)
    
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_email_verification_token(token: str) -> Optional[str]:
    """
    Verify an email verification token and return the email.
    
    Args:
        token: Email verification token
        
    Returns:
        Optional[str]: Email address if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_type = payload.get("type")
        
        if token_type != "email_verification":
            return None
            
        email = payload.get("sub")
        return email
        
    except JWTError:
        return None