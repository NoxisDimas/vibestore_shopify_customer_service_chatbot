from pydantic_settings import BaseSettings, SettingsConfigDict  
from pydantic import field_validator
from typing import Optional, Literal, List
from pathlib import Path

def read_secret(secrete_name:str, default:Optional[str]=None):
    secrete_path = Path(f"run/secretes/{secrete_name}")
    if secrete_path.exists():
        return secrete_path.read_text().strip()
    else:
        return default
    
class Settings(BaseSettings):
    @field_validator('*', mode='before')
    @classmethod
    def empty_str_to_none(cls, v:Optional[str]) -> Optional[str]:
        if isinstance(v, str) and v == "":
            return None
        return v
    
    ENVIRONMENT :Literal["dev", "prod"] = "dev"
    ADMIN_PASSWORD: str = "admin123"

    # Agent
    AGENT_NAME: str = "CustomerServiceAgent"
    API_KEY: Optional[str] = None  # Internal API Key for webhooks/admin

    # llm settings
    OPENAI_API_KEY:Optional[str] = None
    OPENAI_MODEL:Optional[str] = None

    GROQ_API_KEY:Optional[str] = None
    GROQ_MODEL:Optional[str] = None

    GOOGLEGENAI_API_KEY:Optional[str] = None
    GOOGLEGENAI_MODEL:Optional[str] = None

    OLLAMA_BASE_URL:Optional[str] = "http://ollama:11434"
    OLLAMA_MODEL:Optional[str] = "llama3.2"

    # embedding model settings
    OPENAI_EMBEDDING_MODEL:Optional[str] = None
    GOOGLEGENAI_EMBEDDING_MODEL:Optional[str] = None
    OLLAMA_EMBEDDING_MODEL:Optional[str] = None

    LLM_MODE: Literal["static", "auto"] = "auto"
    LLM_STATIC_PROVIDER: Optional[str] = "GOOGLEGENAI"

    LLM_PRIORITY_LIST: List[str] = ["openai", "googlegenai", "groq"]

    # Access Token
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None

    # Qdrant Settings
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_PATH: Optional[str] = None 

    # Mem0 Settings
    MEM0_API_KEY: Optional[str] = None
    
    # Airtable Settings
    AIRTABLE_API_KEY: Optional[str] = None
    AIRTABLE_BASE_ID: Optional[str] = None
    AIRTABLE_TABLE_NAME: Optional[str] = None

    # Shopify Settings
    SHOPIFY_STORE: Optional[str] = None
    SHOPIFY_STOREFRONT_ACCESS_TOKEN: Optional[str] = None
    SHOPIFY_ADMIN_ACCESS_TOKEN: Optional[str] = None
    SHOPIFY_SECRET_KEY: Optional[str] = None

    # Postgres (Checkpointer)
    POSTGRES_URI: str = "postgresql://postgres:postgres@localhost:5432/agent_db"

    # LightRAG
    LIGHTRAG_API_URL: str = "http://lightrag:9621"
    
    # Channels
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None

    # LangSmith Tracing
    LANGSMITH_TRACING: Optional[str] = None
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: Optional[str] = None
    LANGSMITH_ENDPOINT: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Override with Docker Secrets if available (production)
        self._load_docker_secrets()
    
    def _load_docker_secrets(self):
        """Load secrets from Docker Swarm secret files if they exist."""
        secret_mappings = {
            "openai_api_key": "OPENAI_API_KEY",
            "groq_api_key": "GROQ_API_KEY",
            "api_key": "API_KEY",
            "postgres_uri": "POSTGRES_URI",
            "qdrant_api_key": "QDRANT_API_KEY",
            "mem0_api_key": "MEM0_API_KEY",
            "whatsapp_access_token": "WHATSAPP_ACCESS_TOKEN",
            "telegram_bot_token": "TELEGRAM_BOT_TOKEN",
            "langsmith_api_key": "LANGSMITH_API_KEY",
            "airtable_api_key": "AIRTABLE_API_KEY",
            "airtable_base_id": "AIRTABLE_BASE_ID",
            "airtable_table_name": "AIRTABLE_TABLE_NAME",
        }
        
        for secret_name, attr_name in secret_mappings.items():
            secret_value = read_secret(secret_name)
            if secret_value:
                object.__setattr__(self, attr_name, secret_value)



def get_settings():
    return Settings()