from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    department: Optional[str] = "SmartBid Procurement Division"

class UserCreate(UserBase):
    password: str
    role_name: str = "Procurement Officer"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool
    role: RoleResponse
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
