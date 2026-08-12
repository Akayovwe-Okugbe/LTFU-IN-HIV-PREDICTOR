from datetime import date
from pydantic import BaseModel, EmailStr, Field, field_validator

class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=40)
    gender: str = Field(min_length=4, max_length=6)
    date_of_birth: date
    password: str = Field(min_length=12, max_length=200)

    @field_validator('email')
    @classmethod
    def normalise_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator('first_name','last_name')
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()

    @field_validator('gender')
    @classmethod
    def validate_gender(cls, value: str) -> str:
        if value not in {'Male','Female'}:
            raise ValueError('Gender must be Male or Female.')
        return value

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'

class GenericResponse(BaseModel):
    message: str
