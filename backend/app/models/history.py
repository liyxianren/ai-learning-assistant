"""History model."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.extensions import db


class History(db.Model):
    __tablename__ = "histories"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    username = db.Column(db.String(64), nullable=True)
    question = db.Column(db.Text, nullable=False)
    parse_result = db.Column(db.JSON, nullable=False)
    solution = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = db.relationship("User", backref=db.backref("histories", lazy=True, cascade="all,delete-orphan"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "userId": self.user_id,
            "username": self.username,
            "question": self.question,
            "parseResult": self.parse_result,
            "solution": self.solution,
            "createdAt": self._to_iso(self.created_at),
        }

    @staticmethod
    def _to_iso(value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.isoformat(timespec="milliseconds") + "Z"
