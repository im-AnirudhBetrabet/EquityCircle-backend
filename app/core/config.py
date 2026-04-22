from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Equity Circle API"
    VERSION     : str = "0.0.1"
    API_V1_STR  : str = "/api/v1"

    SUPABASE_URL: str
    SUPABASE_KEY: str
    SENDER_EMAIL: str
    SENDER_APP_PASSWORD: str

    TEST_GROUP_ID : str
    TEST_COHORT_ID: str

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()