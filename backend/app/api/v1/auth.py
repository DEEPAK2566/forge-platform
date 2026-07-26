from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, UserOut, AuthResponse
from app.services.auth_service import (
    hash_password, verify_password,
    create_access_token, decode_access_token
)

# APIRouter groups related endpoints together
# prefix="/auth" means all routes here start with /auth
# So register becomes POST /auth/register, login becomes POST /auth/login
router = APIRouter(prefix="/auth", tags=["Authentication"])

# OAuth2PasswordBearer reads the "Authorization: Bearer <token>" header automatically
# tokenUrl is where clients get a token from
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db:    Session = Depends(get_db)
) -> User:
    """
    Dependency function — call this in any endpoint to get the logged-in user.
    FastAPI calls it automatically when an endpoint has: user = Depends(get_current_user)
    
    It reads the Bearer token from the Authorization header,
    decodes it, and returns the User from the database.
    Raises 401 if token is missing, invalid, or expired.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload  = decode_access_token(token)
        user_id  = payload.get("sub")
        if not user_id:
            raise credentials_error
    except JWTError:
        raise credentials_error

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise credentials_error
    return user


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """
    POST /auth/register
    Creates a new user account.
    
    Steps:
    1. Check if email is already taken
    2. Hash the password
    3. Save the new user to the database
    4. Create a JWT token
    5. Return token + user info
    """
    # Check if email already exists in the database
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    # Create the new user — hash the password before saving
    new_user = User(
        email           = data.email,
        full_name       = data.full_name,
        hashed_password = hash_password(data.password),
    )
    db.add(new_user)      # add to the session
    db.commit()           # save to the database
    db.refresh(new_user)  # reload from DB to get the auto-generated ID and created_at

    # Create a JWT token for the new user (log them in immediately after registering)
    token = create_access_token({
        "sub":   str(new_user.id),   # "sub" = subject = who this token belongs to
        "email": new_user.email
    })

    return AuthResponse(
        access_token = token,
        token_type   = "bearer",
        user         = UserOut.model_validate(new_user)
    )


@router.post("/login", response_model=AuthResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """
    POST /auth/login
    Authenticates an existing user.
    
    Steps:
    1. Find user by email
    2. Verify the password against the stored hash
    3. Create a JWT token
    4. Return token + user info
    """
    # Find user by email
    user = db.query(User).filter(User.email == data.email).first()

    # verify_password returns False if user doesn't exist or password is wrong
    # We check both in one condition to avoid revealing which one failed
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = create_access_token({
        "sub":   str(user.id),
        "email": user.email
    })

    return AuthResponse(
        access_token = token,
        token_type   = "bearer",
        user         = UserOut.model_validate(user)
    )


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """
    GET /auth/me
    Returns the profile of whoever is currently logged in.
    Uses the get_current_user dependency — reads the Bearer token automatically.
    The frontend calls this on startup to check if the stored token is still valid.
    """
    return current_user