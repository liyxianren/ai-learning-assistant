"""Problem APIs blueprint."""

from __future__ import annotations

import base64
import json
from datetime import datetime

from flask import Blueprint, Response, current_app, jsonify, request, stream_with_context
from flask_jwt_extended import decode_token

from app.extensions import db
from app.models.user import User
from app.schemas.problem import ParseSchema, RecognizeSchema, SolveProblemSchema, SolveSchema, SolveStreamSchema
from app.services.pipeline_service import pipeline_service


bp = Blueprint("api", __name__)

recognize_schema = RecognizeSchema()
parse_schema = ParseSchema()
solve_schema = SolveSchema()
solve_problem_schema = SolveProblemSchema()
solve_stream_schema = SolveStreamSchema()


def _iso_now() -> str:
    return datetime.utcnow().isoformat(timespec="milliseconds") + "Z"


def _optional_user_identity() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        return None

    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0] != "Bearer":
        return None

    token = parts[1]
    try:
        decoded = decode_token(token)
        return decoded.get("sub")
    except Exception:  # noqa: BLE001
        return None


@bp.get("/health")
def health():
    return jsonify(
        {
            "success": True,
            "message": "服务正常运行",
            "timestamp": _iso_now(),
        }
    )


@bp.post("/recognize")
def recognize():
    payload = recognize_schema.load(request.get_json(silent=True) or {})
    image = payload["image"]

    try:
        body = image.split(",", 1)[1] if "," in image else image
        size_in_bytes = len(base64.b64decode(body, validate=False))
    except Exception:  # noqa: BLE001
        return jsonify({"success": False, "error": "缺少图片数据"}), 400

    if size_in_bytes > current_app.config.get("MAX_IMAGE_SIZE", 5 * 1024 * 1024):
        return jsonify({"success": False, "error": "图片大小超过限制"}), 400

    result = pipeline_service.recognize_only(image)
    return jsonify(result)


@bp.post("/parse")
def parse_problem():
    payload = parse_schema.load(request.get_json(silent=True) or {})
    result = pipeline_service.parse_only(payload["text"])
    return jsonify(result)


@bp.post("/solve")
def solve_problem_part():
    payload = solve_schema.load(request.get_json(silent=True) or {})
    result = pipeline_service.solve_only(payload["text"], payload["parse_result"])
    return jsonify(result)


@bp.post("/solve-problem")
def solve_problem_full():
    payload = solve_problem_schema.load(request.get_json(silent=True) or {})

    user_id = _optional_user_identity()
    username = None
    if user_id:
        user = db.session.get(User, user_id)
        if user:
            username = user.username
        else:
            user_id = None

    result = pipeline_service.solve_problem(
        {
            "type": payload["type"],
            "content": payload["content"],
            "userId": user_id,
            "username": username,
        }
    )

    return jsonify(result)


@bp.post("/solve-stream")
def solve_stream():
    payload = solve_stream_schema.load(request.get_json(silent=True) or {})

    text = payload["text"]
    parse_result = payload["parse_result"]

    @stream_with_context
    def generate():
        try:
            for chunk in pipeline_service.solve_stream(text, parse_result):
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\\n\\n"
            yield "data: [DONE]\\n\\n"
        except Exception as exc:  # noqa: BLE001
            yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\\n\\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
