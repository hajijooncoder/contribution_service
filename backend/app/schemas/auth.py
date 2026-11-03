from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class UserRegister(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2, max_length=255)

    # Forbid extra fields to prevent injection of 'role' or any unallowed parameters
    model_config = ConfigDict(extra="forbid")

class UserRoleUpdate(BaseModel):
    role: str = Field(..., description="Role to assign: contributor, reviewer, admin")

    model_config = ConfigDict(extra="forbid")

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str

class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
