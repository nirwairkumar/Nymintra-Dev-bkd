from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Nymintra API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "SUPER_SECRET_KEY_FOR_JWT_PLEASE_CHANGE_IN_PROD"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # SUPABASE CREDENTIALS
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # FRONTEND (Comma-separated for multiple origins)
    FRONTEND_URLS: str = "http://localhost:3000,http://localhost:5173,https://nymintra.pages.dev"
    
    @property
    def cors_origins(self) -> list[str]:
        return [url.strip() for url in self.FRONTEND_URLS.split(",") if url.strip()]
    
    # RAZORPAY
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""

    # Pydantic configuration
    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()
