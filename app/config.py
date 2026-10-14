from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    ai_provider: str = "mock"
    aws_region: str = "us-west-2"
    bedrock_model_id: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    databricks_host: str = ""
    databricks_token: str = ""
    databricks_endpoint: str = ""
    log_level: str = "INFO"

settings = Settings()
