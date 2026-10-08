"""
Central configuration, loaded from environment variables / .env.
No secrets are ever hard-coded here.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # reads a local .env file if present


def _get_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai").lower()

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_EMBED_MODEL: str = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

    HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "")
    HF_MODEL: str = os.getenv("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct")

    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "3"))
    INTERVIEW_LENGTH: int = int(os.getenv("INTERVIEW_LENGTH", "5"))

    @classmethod
    def effective_provider(cls) -> str:
        """
        Decide which backend actually gets used.
        Falls back to 'mock' automatically if no real credentials are
        configured, so the app never hard-crashes when a key is missing --
        it degrades to an offline demo mode instead.
        """
        if cls.LLM_PROVIDER == "openai" and cls.OPENAI_API_KEY:
            return "openai"
        if cls.LLM_PROVIDER == "huggingface" and cls.HF_API_TOKEN:
            return "huggingface"
        return "mock"

    @classmethod
    def has_real_credentials(cls) -> bool:
        return cls.effective_provider() != "mock"
