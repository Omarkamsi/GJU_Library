from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str
    app_base_url: str = "http://localhost:8080"
    session_secret: str
    session_cookie_name: str = "gju_session"
    session_ttl_hours: int = 8
    allowed_email_domains: str = "gju.edu.jo"
    llm_provider: str = "ollama"
    ollama_host: str = "http://ollama:11434"
    ollama_model: str = "qwen2.5:3b-instruct"
    ollama_keep_alive: str = "30m"
    embedding_model: str = "BAAI/bge-m3"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    retrieve_topk_lexical: int = 50
    retrieve_topk_semantic: int = 50
    rrf_k: int = 60
    rerank_topk: int = 20
    final_topk: int = 5
    db_suggestions_max: int = 3
    user_id_pepper: str
    admin_emails: str = ""

    @property
    def allowed_domains_list(self) -> list[str]:
        return [d.strip().lower() for d in self.allowed_email_domains.split(",") if d.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
