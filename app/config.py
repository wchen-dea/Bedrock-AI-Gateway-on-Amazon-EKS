from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    ai_provider: str = "mock"
    aws_region: str = "us-west-2"
    bedrock_model_id: str = ""
    log_level: str = "INFO"

settings = Settings()
