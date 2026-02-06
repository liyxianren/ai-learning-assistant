"""User model."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    password_legacy = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password, method="pbkdf2:sha256")
        self.password_legacy = None

    def check_password(self, raw_password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, raw_password)

    def check_legacy_password(self, raw_password: str) -> bool:
        if not self.password_legacy:
            return False
        hashed = hashlib.sha256(raw_password.encode("utf-8")).hexdigest()
        return hashed == self.password_legacy

    def verify_and_upgrade_password(self, raw_password: str) -> bool:
        if self.check_password(raw_password):
            return True

        if self.check_legacy_password(raw_password):
            self.set_password(raw_password)
            return True

        return False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "createdAt": self._to_iso(self.created_at),
            "lastLoginAt": self._to_iso(self.last_login_at),
        }

    @staticmethod
    def _to_iso(value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.isoformat(timespec="milliseconds") + "Z"
