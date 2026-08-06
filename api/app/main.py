from fastapi import FastAPI
from app.api.router import api_router
from app.api.routes.patients import SYNTHETIC_NOTICE
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version='0.1.0',
              description='Secure decision-support prototype using synthetic HIV records. Not a diagnostic system.')
app.include_router(api_router)

@app.get('/health', tags=['System'])
def health_check():
    return {
        'status': 'healthy',
        'application': settings.app_name,
        'synthetic_data_only': settings.synthetic_data_only,
        'clinical_disclaimer': 'Decision-support and resource-prioritisation only; not diagnosis or autonomous clinical decision-making.',
        'synthetic_data_notice': SYNTHETIC_NOTICE,
    }
