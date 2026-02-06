"""Migrate legacy JSON data into SQLite tables."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.history import History  # noqa: E402
from app.models.user import User  # noqa: E402


def load_json(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_time(value: str | None):
    if not value:
        return None
    try:
        # JavaScript ISO: 2026-02-03T12:10:47.891Z
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def looks_like_sha256_hash(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{64}", value or ""))


def migrate_users(users_path: Path):
    users_data = load_json(users_path)
    inserted = 0
    skipped = 0

    for item in users_data:
        user_id = item.get("id")
        username = item.get("username")
        password = item.get("password")

        if not user_id or not username:
            skipped += 1
            continue

        exists = User.query.filter((User.id == user_id) | (User.username == username)).first()
        if exists:
            skipped += 1
            continue

        user = User(
            id=user_id,
            username=username,
            created_at=parse_time(item.get("createdAt")) or datetime.utcnow(),
            last_login_at=parse_time(item.get("lastLoginAt")),
        )

        if password:
            if looks_like_sha256_hash(password):
                user.password_legacy = password
            else:
                user.password_hash = password

        db.session.add(user)
        inserted += 1

    db.session.commit()
    return inserted, skipped


def migrate_history(history_path: Path):
    history_data = load_json(history_path)
    inserted = 0
    skipped = 0

    for item in history_data:
        record_id = item.get("id")
        user_id = item.get("userId")
        question = item.get("question")

        if not record_id or not user_id or not question:
            skipped += 1
            continue

        if History.query.filter_by(id=record_id).first():
            skipped += 1
            continue

        user = db.session.get(User, user_id)
        if not user:
            skipped += 1
            continue

        record = History(
            id=record_id,
            user_id=user_id,
            username=item.get("username"),
            question=question,
            parse_result=item.get("parseResult") or {},
            solution=item.get("solution") or {},
            created_at=parse_time(item.get("createdAt")) or datetime.utcnow(),
        )

        db.session.add(record)
        inserted += 1

    db.session.commit()
    return inserted, skipped


def main():
    app = create_app()
    data_dir = PROJECT_ROOT / "data"

    with app.app_context():
        db.create_all()

        user_inserted, user_skipped = migrate_users(data_dir / "users.json")
        history_inserted, history_skipped = migrate_history(data_dir / "history.json")

    print("JSON -> SQLite 迁移完成")
    print(f"用户: 新增 {user_inserted}, 跳过 {user_skipped}")
    print(f"历史: 新增 {history_inserted}, 跳过 {history_skipped}")


if __name__ == "__main__":
    main()
