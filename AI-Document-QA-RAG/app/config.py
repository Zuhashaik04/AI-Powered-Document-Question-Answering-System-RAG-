from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Document QA RAG"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_store_dir: str = "data/faiss_index"
    upload_dir: str = "data/uploads"
    chunk_size: int = 1000
    chunk_overlap: int = 150
    retrieval_k: int = 4
    kafka_enabled: bool = False
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "document-ingested"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def prepare_directories(self) -> None:
        Path(self.vector_store_dir).parent.mkdir(parents=True, exist_ok=True)
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
