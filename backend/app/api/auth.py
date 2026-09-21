from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from app.models.user import User
from app.models.role import Role
from app.schemas.user_schema import UserLogin, UserCreate, UserResponse, Token
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])
security_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Extract and validate current authenticated user from Bearer token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email: str = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User associated with token not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
        
    return user

def require_role(allowed_roles: list[str]):
    """Enforce Role-Based Access Control (RBAC)."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Action requires one of {allowed_roles} role(s). Current role is '{current_user.role.name}'."
            )
        return current_user
    return role_checker

# Dependency specifically requiring the 'Procurement Officer' role
require_procurement_officer = require_role(["Procurement Officer", "Admin"])

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user with email & password and return a signed JWT token."""
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Contact SmartBid administrator."
        )

    # Issue JWT token
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.name, "uid": user.id}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get profile of currently logged-in user."""
    return current_user

@router.post("/register", response_model=UserResponse)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user (with role assignment)."""
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )
    
    role = db.query(Role).filter(Role.name == user_in.role_name).first()
    if not role:
        # Create role if doesn't exist yet
        role = Role(name=user_in.role_name, description=f"{user_in.role_name} role")
        db.add(role)
        db.commit()
        db.refresh(role)

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role_id=role.id,
        department=user_in.department or "SmartBid Procurement Division",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
