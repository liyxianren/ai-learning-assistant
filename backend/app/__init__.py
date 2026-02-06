"""Flask application factory."""

from __future__ import annotations

import os

from flask import Flask, jsonify

from app.blueprints.api import bp as api_bp
from app.blueprints.auth import bp as auth_bp
from app.blueprints.history import bp as history_bp
from app.config import config as config_map
from app.extensions import cors, db, jwt, limiter
from app.utils.errors import register_error_handlers


def _rate_limit_rule(max_requests: int, window_seconds: int) -> str:
    if window_seconds % 60 == 0:
        minutes = max(1, window_seconds // 60)
        unit = "minute" if minutes == 1 else "minutes"
        return f"{max_requests} per {minutes} {unit}"
    unit = "second" if window_seconds == 1 else "seconds"
    return f"{max_requests} per {window_seconds} {unit}"


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)

    env_name = config_name or os.getenv("FLASK_ENV", os.getenv("NODE_ENV", "development"))
    app.config.from_object(config_map.get(env_name, config_map["default"]))
    app.json.ensure_ascii = False

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGIN"]}},
        supports_credentials=True,
    )
    app.config["RATELIMIT_DEFAULT"] = _rate_limit_rule(
        app.config["RATE_LIMIT_MAX_REQUESTS"],
        app.config["RATE_LIMIT_WINDOW_SECONDS"],
    )
    limiter.init_app(app)

    @jwt.unauthorized_loader
    def unauthorized_loader(reason):
        if "Bearer" in reason or "Authorization header" in reason:
            message = "认证令牌格式无效"
        else:
            message = "未提供认证令牌"
        return jsonify({"success": False, "error": message}), 401

    @jwt.invalid_token_loader
    def invalid_token_loader(reason):
        if "Authorization" in reason or "Bearer" in reason:
            error_message = "认证令牌格式无效"
        else:
            error_message = "认证令牌无效"
        return jsonify({"success": False, "error": error_message}), 401

    @jwt.expired_token_loader
    def expired_token_loader(_jwt_header, _jwt_payload):
        return jsonify({"success": False, "error": "认证令牌已过期"}), 401

    @jwt.needs_fresh_token_loader
    def needs_fresh_token_loader(_jwt_header, _jwt_payload):
        return jsonify({"success": False, "error": "认证令牌无效"}), 401

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(history_bp, url_prefix="/api/history")

    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app
