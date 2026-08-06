from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    app_name: str = 'MEDISCOPE'
    environment: str = 'development'
    database_url: str = 'postgresql+psycopg://mediscope:change-me@localhost:5432/mediscope'
    secret_key: str = Field(default='CHANGE-THIS-WITH-A-LONG-RANDOM-SECRET-KEY', min_length=32)
    jwt_algorithm: str = 'HS256'
    access_token_expire_minutes: int = 30
    password_min_length: int = 12
    synthetic_data_only: bool = True
    logistic_model_path: str = 'models/trained/logistic_regression_pipeline.joblib'
    xgboost_model_path: str = 'models/trained/xgboost_pipeline.joblib'
    decision_threshold: float = 0.50

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
