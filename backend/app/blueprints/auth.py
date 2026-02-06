"""Auth blueprint."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from app.extensions import db
from app.models.user import User
from app.schemas.auth import LoginSchema, RegisterSchema


bp = Blueprint("auth", __name__)

register_schema = RegisterSchema()
login_schema = LoginSchema()


@bp.post("/register")
def register():
    payload = register_schema.load(request.get_json(silent=True) or {})

    existing_user = User.query.filter_by(username=payload["username"]).first()
    if existing_user:
        return jsonify({"success": False, "error": "用户名已存在"}), 409

    user = User(username=payload["username"])
    user.set_password(payload["password"])

    db.session.add(user)
    db.session.commit()

    return (
        jsonify(
            {
                "success": True,
                "message": "注册成功",
                "data": {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "createdAt": user.to_dict()["createdAt"],
                    }
                },
            }
        ),
        201,
    )


@bp.post("/login")
def login():
    payload = login_schema.load(request.get_json(silent=True) or {})

    username = payload["username"]
    password = payload["password"]

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"success": False, "error": "用户名或密码错误"}), 401

    if not user.verify_and_upgrade_password(password):
        return jsonify({"success": False, "error": "用户名或密码错误"}), 401

    user.last_login_at = datetime.utcnow()
    db.session.commit()

    token = create_access_token(
        identity=user.id,
        additional_claims={"username": user.username},
    )

    return jsonify(
        {
            "success": True,
            "message": "登录成功",
            "data": {
                "token": token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                },
            },
        }
    )


@bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"success": False, "error": "用户不存在"}), 404

    return jsonify(
        {
            "success": True,
            "data": {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "createdAt": user.to_dict()["createdAt"],
                    "lastLoginAt": user.to_dict()["lastLoginAt"],
                }
            },
        }
    )


@bp.post("/logout")
def logout():
    return jsonify({"success": True, "message": "登出成功"})
