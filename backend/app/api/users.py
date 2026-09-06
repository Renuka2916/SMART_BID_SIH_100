from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from app.models.user import User
from app.models.role import Role
from app.schemas.user_schema import UserResponse, RoleResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/users", tags=["User & Role Management"])

@router.get("", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List system users."""
    return db.query(User).all()

@router.get("/roles", response_model=List[RoleResponse])
def list_roles(db: Session = Depends(get_db)):
    """List available system roles."""
    return db.query(Role).all()
