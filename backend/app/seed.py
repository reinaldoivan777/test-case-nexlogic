from flask import current_app

from .extensions import db
from .models import KnowledgeBase, KnowledgeChunk
from .services.embedding_service import EmbeddingService


SEED_CHUNKS = [
    {
        "document_name": "Nexlogic Overview.md",
        "content": "Nexlogic Studio is a visual AI workflow platform. Users compose workflows from nodes for retrieval, LLM generation, agents, tools, and typed output.",
    },
    {
        "document_name": "Knowledge Retrieval.md",
        "content": "A RAG workflow retrieves the most relevant document chunks, constructs a context prompt, and sends that context with the user query to a language model.",
    },
    {
        "document_name": "Workflow Builder.md",
        "content": "The workflow builder uses ReactFlow. A valid starter RAG graph connects Start to Knowledge Retrieval, then LLM, then Answer.",
    },
    {
        "document_name": "Platform Architecture.md",
        "content": "Nexlogic separates the React frontend, Flask API, persistence layer, and external LLM or MCP integrations. The backend protects provider credentials.",
    },
    {
        "document_name": "RAG Quality.md",
        "content": "Answer quality depends on relevant citations, clear prompt context, suitable top-k retrieval, and graceful handling when the language model is unavailable.",
    },
]


def seed_database():
    if KnowledgeBase.query.first():
        return

    knowledge_base = KnowledgeBase(
        id="nexlogic-handbook",
        name="Nexlogic Handbook",
        description="Seed documents for the Mini RAG Workflow Builder assessment.",
    )
    embedding_service = EmbeddingService()
    db.session.add(knowledge_base)
    for index, chunk in enumerate(SEED_CHUNKS):
        chunk["embedding"] = (
            [float(index + 1)]
            if current_app.config.get("TESTING")
            else embedding_service.generate_embedding(chunk["content"])
        )
        db.session.add(KnowledgeChunk(knowledge_base_id=knowledge_base.id, **chunk))
    db.session.commit()
