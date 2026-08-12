from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone: str | None
    gender: str | None
    date_of_birth: date | None
    role: str
    account_status: str
    email_verified_at: datetime | None
    mfa_enabled: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

class UserSelfUpdateRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=2, max_length=100)
    last_name: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=40)
    gender: str | None = None
    date_of_birth: date | None = None

    @field_validator('first_name','last_name')
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        return None if value is None else value.strip()

    @field_validator('gender')
    @classmethod
    def validate_gender(cls, value: str | None) -> str | None:
        if value is not None and value not in {'Male','Female'}:
            raise ValueError('Gender must be Male or Female.')
        return value
