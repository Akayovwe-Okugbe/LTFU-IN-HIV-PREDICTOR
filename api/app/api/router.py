from fastapi import APIRouter
from .routes import auth, patients, users
api_router = APIRouter(prefix='/api/v1')
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(patients.router)
