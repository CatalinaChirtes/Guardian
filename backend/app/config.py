from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""

    # database (Supabase PostgreSQL)
    database_url: str = ""
    db_pool_size: int = 5
    db_max_overflow: int = 5

    # LLM providers
    openai_api_key: str = ""
    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    default_llm_provider: str = "gemini"

    # RAG
    embedding_model: str = "all-MiniLM-L6-v2"
    faiss_index_path: str = "./data/faiss_index"

    # tutor settings
    max_attempts_before_puzzle: int = 10
    chat_history_window: int = 4

    # experiment flags (all default to True for production, set to False in .env for ablation experiments)
    enable_socratic_prompt: bool = True
    enable_code_police: bool = True
    enable_rag: bool = True

    # CORS
    cors_origins: list[str] = ["http://localhost:4200"]

    # registration mode: "allowlist" (study - only pre-approved emails), "domain" (presentation - any @e-uvt.ro)
    registration_mode: str = "allowlist"
    allowed_email_domain: str = "e-uvt.ro"

    # admin emails (comma-separated in .env)
    admin_emails: list[str] = []

    # HuggingFace
    hf_token: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
