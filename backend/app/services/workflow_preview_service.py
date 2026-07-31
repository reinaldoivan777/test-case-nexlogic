from datetime import datetime, timezone

from ..extensions import db
from ..models import KnowledgeBase, WorkflowRun
from .llm_service import LlmService
from .rag_service import RagService


class ValidationError(Exception):
    pass


class NotFoundError(Exception):
    pass


EXPECTED_PATH = [
    ("start", "retrieval"),
    ("retrieval", "llm"),
    ("llm", "answer"),
]


class WorkflowPreviewService:
    def preview(self, payload):
        if not isinstance(payload, dict):
            raise ValidationError("Request body must be a JSON object")

        workflow_id = payload.get("workflow_id") or "default"
        query = self._validate_query(payload.get("query"))
        nodes = self._validate_nodes(payload.get("nodes"))
        self._validate_edges(payload.get("edges"))

        retrieval_data = nodes["retrieval"].get("data") or {}
        llm_data = nodes["llm"].get("data") or {}
        knowledge_base_id = self._validate_knowledge_base_id(retrieval_data.get("knowledge_base_id"))
        top_k = self._validate_top_k(retrieval_data.get("top_k"))

        if not db.session.get(KnowledgeBase, knowledge_base_id):
            raise NotFoundError("Knowledge base not found")

        retrieved_chunks = RagService().retrieve(knowledge_base_id, query, top_k)
        citations = [
            {
                "chunk_id": chunk["chunk_id"],
                "document_name": chunk["document_name"],
                "score": chunk["score"],
            }
            for chunk in retrieved_chunks
        ]
        prompt = self._build_prompt(query, retrieved_chunks, llm_data.get("prompt_template"))
        answer = LlmService().generate(prompt)
        trace = [
            {"node_id": "start", "status": "succeeded"},
            {"node_id": "retrieval", "status": "succeeded", "retrieved_count": len(retrieved_chunks)},
            {"node_id": "llm", "status": "succeeded"},
            {"node_id": "answer", "status": "succeeded"},
        ]

        run = WorkflowRun(
            workflow_id=workflow_id,
            query=query,
            answer=answer,
            citations=citations,
            trace=trace,
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(run)
        db.session.commit()
        return run

    def _validate_query(self, query):
        if not isinstance(query, str) or not query.strip():
            raise ValidationError("Query is required")
        return query.strip()

    def _validate_nodes(self, nodes):
        if not isinstance(nodes, list):
            raise ValidationError("Nodes must be provided")

        by_id = {node.get("id"): node for node in nodes if isinstance(node, dict)}
        missing = [node_id for node_id in ("start", "retrieval", "llm", "answer") if node_id not in by_id]
        if missing:
            raise ValidationError("Graph must include Start, Retrieval, LLM, and Answer nodes")

        for node_id in ("start", "retrieval", "llm", "answer"):
            if by_id[node_id].get("type") != node_id:
                raise ValidationError("Graph contains an invalid node type")

        return by_id

    def _validate_edges(self, edges):
        if not isinstance(edges, list):
            raise ValidationError("Edges must be provided")

        pairs = {(edge.get("source"), edge.get("target")) for edge in edges if isinstance(edge, dict)}
        if any(pair not in pairs for pair in EXPECTED_PATH):
            raise ValidationError("Graph must connect Start → Retrieval → LLM → Answer")

    def _validate_knowledge_base_id(self, knowledge_base_id):
        if not isinstance(knowledge_base_id, str) or not knowledge_base_id.strip():
            raise ValidationError("knowledge_base_id is required")
        return knowledge_base_id.strip()

    def _validate_top_k(self, top_k):
        try:
            value = int(top_k)
        except (TypeError, ValueError):
            raise ValidationError("top_k must be a number")
        if value < 1 or value > 5:
            raise ValidationError("top_k must be between 1 and 5")
        return value

    def _build_prompt(self, query, chunks, prompt_template):
        instruction = (
            prompt_template.strip()
            if isinstance(prompt_template, str) and prompt_template.strip()
            else "Answer the question using only the supplied context."
        )
        context = "\n\n".join(
            f"[{index}] {chunk['document_name']} (score: {chunk['score']}):\n{chunk['content']}"
            for index, chunk in enumerate(chunks, start=1)
        )
        return (
            f"{instruction}\n\n"
            f"Context:\n{context or 'No context was retrieved.'}\n\n"
            f"Question:\n{query}\n\n"
            "Answer:"
        )
