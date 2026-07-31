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
EXPECTED_NODE_IDS = {"start", "retrieval", "llm", "answer"}
EXPECTED_EDGE_PAIRS = set(EXPECTED_PATH)
PROMPT_INSTRUCTION = "Answer the question using only the supplied context."
MAX_QUERY_LENGTH = 500
MAX_WORKFLOW_ID_LENGTH = 64
MAX_CONTEXT_CHARS = 6000
MAX_PROMPT_CHARS = 8000


class WorkflowPreviewService:
    def preview(self, payload):
        if not isinstance(payload, dict):
            raise ValidationError("Request body must be a JSON object")

        workflow_id = self._validate_workflow_id(payload.get("workflow_id"))
        query = self._validate_query(payload.get("query"))
        nodes = self._validate_nodes(payload.get("nodes"))
        self._validate_edges(payload.get("edges"))

        retrieval_data = nodes["retrieval"].get("data") or {}
        knowledge_base_id = self._validate_knowledge_base_id(retrieval_data.get("knowledge_base_id"))
        top_k = self._validate_top_k(retrieval_data.get("top_k"))

        if not db.session.get(KnowledgeBase, knowledge_base_id):
            raise NotFoundError("Knowledge base not found")

        try:
            retrieved_chunks = RagService().retrieve(knowledge_base_id, query, top_k)
        except ValueError as error:
            raise NotFoundError(str(error)) from error
        citations = [
            {
                "chunk_id": chunk["chunk_id"],
                "document_name": chunk["document_name"],
                "score": chunk["score"],
            }
            for chunk in retrieved_chunks
        ]
        prompt = self._build_prompt(query, retrieved_chunks)
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
        value = query.strip()
        if len(value) > MAX_QUERY_LENGTH:
            raise ValidationError(f"Query must be {MAX_QUERY_LENGTH} characters or fewer")
        return value

    def _validate_workflow_id(self, workflow_id):
        value = "default" if workflow_id is None or workflow_id == "" else workflow_id
        if not isinstance(value, str):
            raise ValidationError("workflow_id must be a string")
        if len(value) > MAX_WORKFLOW_ID_LENGTH:
            raise ValidationError(f"workflow_id must be {MAX_WORKFLOW_ID_LENGTH} characters or fewer")
        if value != "default":
            raise ValidationError("workflow_id must be default")
        return value

    def _validate_nodes(self, nodes):
        if not isinstance(nodes, list):
            raise ValidationError("Nodes must be provided")
        if len(nodes) != len(EXPECTED_NODE_IDS):
            raise ValidationError("Graph must contain exactly Start, Retrieval, LLM, and Answer nodes")

        by_id = {node.get("id"): node for node in nodes if isinstance(node, dict)}
        if len(by_id) != len(nodes):
            raise ValidationError("Graph contains duplicate or invalid nodes")
        if set(by_id) != EXPECTED_NODE_IDS:
            raise ValidationError("Graph must contain exactly Start, Retrieval, LLM, and Answer nodes")

        for node_id in EXPECTED_NODE_IDS:
            if by_id[node_id].get("type") != node_id:
                raise ValidationError("Graph contains an invalid node type")

        return by_id

    def _validate_edges(self, edges):
        if not isinstance(edges, list):
            raise ValidationError("Edges must be provided")
        if len(edges) != len(EXPECTED_EDGE_PAIRS):
            raise ValidationError("Graph must contain exactly Start → Retrieval → LLM → Answer edges")

        pairs = {(edge.get("source"), edge.get("target")) for edge in edges if isinstance(edge, dict)}
        if len(pairs) != len(edges):
            raise ValidationError("Graph contains duplicate or invalid edges")
        if pairs != EXPECTED_EDGE_PAIRS:
            raise ValidationError("Graph must connect exactly Start → Retrieval → LLM → Answer")

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

    def _build_prompt(self, query, chunks):
        context = self._build_context(chunks)
        prompt = (
            f"{PROMPT_INSTRUCTION}\n\n"
            f"Context:\n{context or 'No context was retrieved.'}\n\n"
            f"Question:\n{query}\n\n"
            "Answer:"
        )
        if len(prompt) > MAX_PROMPT_CHARS:
            raise ValidationError("Prompt exceeds the maximum allowed size")
        return prompt

    def _build_context(self, chunks):
        parts = []
        remaining = MAX_CONTEXT_CHARS
        for index, chunk in enumerate(chunks, start=1):
            header = f"[{index}] {chunk['document_name']} (score: {chunk['score']}):\n"
            if len(header) >= remaining:
                break

            available_content_chars = remaining - len(header)
            content = chunk["content"][:available_content_chars]
            part = f"{header}{content}"
            parts.append(part)
            remaining -= len(part) + 2
            if remaining <= 0:
                break
        return "\n\n".join(parts)
