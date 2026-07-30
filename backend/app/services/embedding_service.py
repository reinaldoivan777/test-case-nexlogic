import requests
from flask import current_app


class EmbeddingUnavailableError(Exception):
    pass


class EmbeddingService:
    def generate_embedding(self, text, is_query=False):
        base_url = current_app.config["OLLAMA_BASE_URL"]
        model = current_app.config["OLLAMA_EMBEDDING_MODEL"]
        if not base_url or not model:
            raise EmbeddingUnavailableError("Embedding provider is not configured")

        prefix = "search_query: " if is_query else "search_document: "
        headers = {"Content-Type": "application/json"}
        auth_header = current_app.config["NGROK_AUTH_HEADER"]
        if auth_header:
            headers["Authorization"] = auth_header

        try:
            response = requests.post(
                f"{base_url}/api/embed",
                headers=headers,
                json={"model": model, "input": f"{prefix}{text}"},
                timeout=current_app.config["EMBEDDING_TIMEOUT_SECONDS"],
            )
            response.raise_for_status()
            payload = response.json()
            embedding = payload.get("embeddings", [payload.get("embedding")])[0]
        except (requests.RequestException, ValueError, IndexError, TypeError) as error:
            raise EmbeddingUnavailableError("Embedding provider is unavailable") from error

        if not isinstance(embedding, list) or not embedding:
            raise EmbeddingUnavailableError("Embedding provider returned an invalid vector")
        return embedding
