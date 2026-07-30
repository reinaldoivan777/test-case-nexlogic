import math

from ..models import KnowledgeBase, KnowledgeChunk
from .embedding_service import EmbeddingService


class RagService:
    def retrieve(self, knowledge_base_id, query, top_k):
        knowledge_base = db_get_knowledge_base(knowledge_base_id)
        if not knowledge_base:
            raise ValueError("Knowledge base not found")

        query_embedding = self._embed_query(query)
        chunks = KnowledgeChunk.query.filter_by(knowledge_base_id=knowledge_base_id).all()
        ranked_chunks = sorted(
            (
                {
                    "chunk_id": chunk.id,
                    "document_name": chunk.document_name,
                    "content": chunk.content,
                    "score": round(self._cosine_similarity(query_embedding, chunk.embedding), 4),
                }
                for chunk in chunks
            ),
            key=lambda item: item["score"],
            reverse=True,
        )
        return ranked_chunks[:top_k]

    def _embed_query(self, query):
        return EmbeddingService().generate_embedding(query, is_query=True)

    def _cosine_similarity(self, left, right):
        dot_product = sum(a * b for a, b in zip(left, right))
        magnitude_left = math.sqrt(sum(a * a for a in left))
        magnitude_right = math.sqrt(sum(b * b for b in right))
        if not magnitude_left or not magnitude_right:
            return 0.0
        return dot_product / (magnitude_left * magnitude_right)


def db_get_knowledge_base(knowledge_base_id):
    return KnowledgeBase.query.get(knowledge_base_id)
