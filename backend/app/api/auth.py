from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.auth import LoginRequest, Token, UserResponse, UserCreate
from app.services.auth_service import AuthService
from app.core.security import create_access_token
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user with email and password, returning JWT access token."""
    user = AuthService.authenticate_user(db, email=login_data.email, password=login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(subject=user.id, role=user.role.value)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get the profile of the currently logged in user."""
    return current_user


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    # Allow registration if database is empty, otherwise require admin
    current_admin: User = Depends(get_current_admin)
):
    """Create a new user (admin-only)."""
    existing_user = AuthService.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    return AuthService.create_user(db, user_in)
