# We now use bcrypt directly instead of passlib
# bcrypt is already installed — it was a dependency of passlib
import bcrypt
from jose import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings


def hash_password(plain_password: str) -> str:
    """
    Converts a plain password into a bcrypt hash for safe storage.
    
    Why bcrypt: it is deliberately slow — makes brute force attacks take years.
    Even if someone steals your database, they cannot reverse the hashes.
    
    encode('utf-8')      → converts string to bytes (bcrypt needs bytes)
    gensalt(rounds=12)   → generates a random salt — makes every hash unique
                           even if two users have the same password
    hashpw()             → performs the actual hashing
    decode('utf-8')      → converts bytes back to string for DB storage
    """
    password_bytes = plain_password.encode('utf-8')
    salt   = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if a plain password matches a stored hash.
    Returns True if they match, False if not.
    
    checkpw() re-hashes the plain password with the same salt
    that was embedded in the stored hash, then compares the results.
    This is the only safe way to verify bcrypt passwords.
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes   = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict) -> str:
    """
    Creates a signed JWT token containing the provided data.
    
    The token encodes: user ID, email, and expiry time.
    It is signed with SECRET_KEY — only our server can verify it.
    If someone tampers with the token contents, verification fails.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Reads and verifies a JWT token.
    Returns the payload dict (user ID, email, etc.).
    Raises JWTError if the token is invalid, tampered with, or expired.
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )