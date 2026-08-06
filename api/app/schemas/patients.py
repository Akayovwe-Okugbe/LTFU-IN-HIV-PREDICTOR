from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class PatientCreate(BaseModel):
    linked_user_id: UUID | None = None
    synthetic_patient_number: str = Field(min_length=3, max_length=50)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date | None = None
    sex: str = Field(min_length=1, max_length=40)
    state: str = Field(min_length=1, max_length=100)
    lga: str = Field(min_length=1, max_length=150)

class PatientRead(PatientCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: str
    is_synthetic: bool
    created_at: datetime
    updated_at: datetime

class AssignmentCreate(BaseModel):
    clinician_user_id: UUID
    patient_id: UUID
