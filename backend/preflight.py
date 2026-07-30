import sys

from app import create_app
from app.services.llm_service import LlmService


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        result = LlmService().preflight()

    print(result["message"])
    sys.exit(0 if result["ready"] else 1)
