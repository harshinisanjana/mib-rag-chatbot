from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate
from app.core.security import get_password_hash, verify_password


class AuthService:
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Fetch a user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Fetch a user by email."""
        return db.query(User).filter(User.email == email.lower().strip()).first()

    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> User:
        """Create a new user with hashed password."""
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            name=user_in.name,
            email=user_in.email.lower().strip(),
            password_hash=hashed_password,
            role=user_in.role
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password."""
        user = AuthService.get_user_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
