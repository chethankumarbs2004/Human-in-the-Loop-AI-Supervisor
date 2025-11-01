# db.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum
import uuid

db = SQLAlchemy()

def gen_uuid():
    return str(uuid.uuid4())

class RequestStatus(str, enum.Enum):
    Pending = "Pending"
    Resolved = "Resolved"
    Unresolved = "Unresolved"

class HelpRequest(db.Model):
    __tablename__ = "help_requests"
    id = db.Column(db.String, primary_key=True, default=gen_uuid)
    question = db.Column(db.Text, nullable=False)
    caller_id = db.Column(db.String, nullable=True)
    status = db.Column(db.Enum(RequestStatus), default=RequestStatus.Pending, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    supervisor_response = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "caller_id": self.caller_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "supervisor_response": self.supervisor_response
        }

class KnowledgeBase(db.Model):
    __tablename__ = "knowledge_base"
    id = db.Column(db.String, primary_key=True, default=gen_uuid)
    question = db.Column(db.Text, nullable=False, unique=True)
    answer = db.Column(db.Text, nullable=False)
    added_on = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "added_on": self.added_on.isoformat()
        }
