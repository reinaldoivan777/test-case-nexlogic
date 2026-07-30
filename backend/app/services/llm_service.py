import requests
from flask import current_app


class LlmUnavailableError(Exception):
    pass


class LlmService:
    def generate(self, prompt):
        base_url = current_app.config["OLLAMA_BASE_URL"]
        model = current_app.config["OLLAMA_CHAT_MODEL"]
        if not base_url or not model:
            raise LlmUnavailableError("LLM provider is not configured")

        headers = {"Content-Type": "application/json"}
        auth_header = current_app.config["NGROK_AUTH_HEADER"]
        if auth_header:
            headers["Authorization"] = auth_header

        try:
            response = requests.post(
                f"{base_url}/api/generate",
                headers=headers,
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=current_app.config["OLLAMA_TIMEOUT_SECONDS"],
            )
            response.raise_for_status()
            answer = response.json().get("response", "").strip()
        except (requests.RequestException, ValueError) as error:
            raise LlmUnavailableError("LLM provider is unavailable") from error

        if not answer:
            raise LlmUnavailableError("LLM provider returned an empty answer")
        return answer

    def preflight(self):
        base_url = current_app.config["OLLAMA_BASE_URL"]
        if not base_url:
            return {"ready": False, "message": "LLM provider is not configured"}
        headers = {}
        auth_header = current_app.config["NGROK_AUTH_HEADER"]
        if auth_header:
            headers["Authorization"] = auth_header
        try:
            response = requests.get(f"{base_url}/api/tags", headers=headers, timeout=5)
            response.raise_for_status()
            available_models = {
                model.get("name")
                for model in response.json().get("models", [])
                if model.get("name")
            }
        except (requests.RequestException, ValueError):
            return {"ready": False, "message": "LLM provider is unavailable"}

        required_models = {
            current_app.config["OLLAMA_CHAT_MODEL"],
            current_app.config["OLLAMA_EMBEDDING_MODEL"],
        }
        missing_models = sorted(required_models - available_models)
        if missing_models:
            return {"ready": False, "message": "A required Ollama model is unavailable"}
        return {"ready": True, "message": "LLM and embedding providers are ready"}
