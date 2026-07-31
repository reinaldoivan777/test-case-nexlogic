from flask import Blueprint, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge

from .extensions import db
from .models import KnowledgeBase, WorkflowRun
from .services.embedding_service import EmbeddingUnavailableError
from .services.llm_service import LlmService, LlmUnavailableError
from .services.workflow_preview_service import NotFoundError, ValidationError, WorkflowPreviewService

api = Blueprint("api", __name__, url_prefix="/api")
CORS(api)

DEFAULT_WORKFLOW = {
    "id": "default",
    "name": "Nexlogic RAG Preview",
    "nodes": [
        {
            "id": "start",
            "type": "start",
            "position": {"x": 40, "y": 160},
            "data": {"label": "Start", "description": "Receives the user query"},
        },
        {
            "id": "retrieval",
            "type": "retrieval",
            "position": {"x": 290, "y": 130},
            "data": {"label": "Knowledge Retrieval", "knowledge_base_id": "", "top_k": 3},
        },
        {
            "id": "llm",
            "type": "llm",
            "position": {"x": 590, "y": 160},
            "data": {"label": "LLM", "prompt_template": "Answer the question using only the supplied context."},
        },
        {
            "id": "answer",
            "type": "answer",
            "position": {"x": 840, "y": 160},
            "data": {"label": "Answer"},
        },
    ],
    "edges": [
        {"id": "start-retrieval", "source": "start", "target": "retrieval"},
        {"id": "retrieval-llm", "source": "retrieval", "target": "llm"},
        {"id": "llm-answer", "source": "llm", "target": "answer"},
    ],
}


def error_response(code, message, status):
    return jsonify({"error": {"code": code, "message": message}}), status


@api.app_errorhandler(RequestEntityTooLarge)
def request_entity_too_large(error):
    return error_response("validation_error", "Request body is too large", 413)


@api.get("/health")
def health():
    return jsonify({"status": "ok"})


@api.get("/preflight")
def preflight():
    return jsonify(LlmService().preflight())


@api.get("/knowledge-bases")
def list_knowledge_bases():
    knowledge_bases = KnowledgeBase.query.order_by(KnowledgeBase.name).all()
    return jsonify({"data": [knowledge_base.to_dict() for knowledge_base in knowledge_bases]})


@api.get("/workflows/default")
def get_default_workflow():
    return jsonify({"data": DEFAULT_WORKFLOW})


@api.post("/workflows/preview")
def preview_workflow():
    payload = request.get_json(silent=True)
    try:
        run = WorkflowPreviewService().preview(payload)
    except ValidationError as error:
        return error_response("validation_error", str(error), 400)
    except NotFoundError as error:
        return error_response("not_found", str(error), 404)
    except (EmbeddingUnavailableError, LlmUnavailableError) as error:
        return error_response("provider_unavailable", str(error), 503)

    return jsonify(run.to_dict()), 201


@api.get("/runs")
def list_runs():
    workflow_id = request.args.get("workflow_id") or "default"
    runs = (
        db.session.query(WorkflowRun)
        .filter_by(workflow_id=workflow_id)
        .order_by(WorkflowRun.created_at.desc())
        .limit(20)
        .all()
    )
    return jsonify({"data": [run.to_dict() for run in runs]})
