import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///nexlogic_test_case.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "").rstrip("/")
    OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "")
    OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:v1.5")
    OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "45"))
    EMBEDDING_TIMEOUT_SECONDS = int(os.getenv("EMBEDDING_TIMEOUT_SECONDS", "60"))
    NGROK_AUTH_HEADER = os.getenv("NGROK_AUTH_HEADER", "")
