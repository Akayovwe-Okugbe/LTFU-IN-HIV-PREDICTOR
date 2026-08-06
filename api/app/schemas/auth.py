from pydantic import BaseModel, EmailStr, Field, field_validator

class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=40)
    gender: str | None = Field(default=None, max_length=40)
    password: str = Field(min_length=12, max_length=200)

    @field_validator('email')
    @classmethod
    def normalise_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'

class GenericResponse(BaseModel):
    message: str
