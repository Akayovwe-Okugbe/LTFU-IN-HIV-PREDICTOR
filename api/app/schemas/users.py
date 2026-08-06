from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone: str | None
    gender: str | None
    role: str
    account_status: str
    mfa_enabled: bool
    created_at: datetime
    updated_at: datetime
