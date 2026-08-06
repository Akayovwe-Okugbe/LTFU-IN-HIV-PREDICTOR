from fastapi import APIRouter
from app.api.dependencies import CurrentUser
from app.schemas.users import UserRead
router = APIRouter(prefix='/users', tags=['Users'])

@router.get('/me', response_model=UserRead)
def read_me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
