from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    use_playwright: bool = True
    playwright_timeout: int = 15
    http_timeout: int = 10
    max_concurrent_playwright: int = 3
    rich_text_max_chars: int = 800
    about_text_max_chars: int = 300
    max_domains_per_request: int = 100
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()
