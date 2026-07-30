from datetime import datetime, timezone
import uuid

from .extensions import db


class KnowledgeBase(db.Model):
    __tablename__ = "knowledge_bases"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    chunks = db.relationship("KnowledgeChunk", backref="knowledge_base", cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description}


class KnowledgeChunk(db.Model):
    __tablename__ = "knowledge_chunks"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_base_id = db.Column(db.String(36), db.ForeignKey("knowledge_bases.id"), nullable=False)
    document_name = db.Column(db.String(160), nullable=False)
    content = db.Column(db.Text, nullable=False)
    embedding = db.Column(db.JSON, nullable=False)


class WorkflowRun(db.Model):
    __tablename__ = "workflow_runs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = db.Column(db.String(64), nullable=False, index=True)
    query = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    citations = db.Column(db.JSON, nullable=False)
    trace = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "query": self.query,
            "answer": self.answer,
            "citations": self.citations,
            "trace": self.trace,
            "created_at": self.created_at.isoformat(),
        }
