from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    port: int = 8080
    nats_url: str = "nats://nats:4222"
    opensearch_url: str = "http://opensearch:9200"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
