"""History blueprint."""

from __future__ import annotations

import math

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models.history import History
from app.schemas.history import HistoryQuerySchema


bp = Blueprint("history", __name__)
query_schema = HistoryQuerySchema()


@bp.get("")
@jwt_required()
def list_history():
    args = query_schema.load(request.args)

    page = args["page"]
    limit = args["limit"]
    user_id = get_jwt_identity()

    query = History.query.filter_by(user_id=user_id).order_by(History.created_at.desc())
    total = query.count()

    records = (
        query.offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return jsonify(
        {
            "success": True,
            "data": {
                "records": [record.to_dict() for record in records],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "totalPages": math.ceil(total / limit) if total > 0 else 0,
                },
            },
        }
    )


@bp.post("")
@jwt_required()
def create_history():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question") or "").strip()
    parse_result = payload.get("parseResult")
    solution = payload.get("solution")

    if not question or not isinstance(parse_result, dict) or not isinstance(solution, dict):
        return jsonify({"success": False, "error": "缺少历史记录数据"}), 400

    user_id = get_jwt_identity()
    record = History(
        user_id=user_id,
        username=payload.get("username"),
        question=question,
        parse_result=parse_result,
        solution=solution,
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({"success": True, "data": {"record": record.to_dict()}}), 201


@bp.get("/<string:record_id>")
@jwt_required()
def get_history(record_id: str):
    user_id = get_jwt_identity()

    record = History.query.filter_by(id=record_id, user_id=user_id).first()
    if not record:
        return jsonify({"success": False, "error": "记录不存在或无权限查看"}), 404

    return jsonify({"success": True, "data": {"record": record.to_dict()}})


@bp.delete("/<string:record_id>")
@jwt_required()
def delete_history(record_id: str):
    user_id = get_jwt_identity()

    record = History.query.filter_by(id=record_id, user_id=user_id).first()
    if not record:
        return jsonify({"success": False, "error": "记录不存在或无权限删除"}), 404

    db.session.delete(record)
    db.session.commit()

    return jsonify({"success": True, "message": "删除成功"})


@bp.delete("")
@jwt_required()
def clear_history():
    user_id = get_jwt_identity()

    History.query.filter_by(user_id=user_id).delete()
    db.session.commit()

    return jsonify({"success": True, "message": "清空历史记录成功"})
