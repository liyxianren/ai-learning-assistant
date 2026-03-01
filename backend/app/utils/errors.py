"""Custom errors and global handlers."""

from __future__ import annotations

from http import HTTPStatus

from flask import jsonify
from marshmallow import ValidationError


class APIError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _json_error(message: str, status_code: int):
    return jsonify({"success": False, "error": message}), status_code


def register_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        return _json_error(error.message, error.status_code)

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        message = "参数校验失败"
        if isinstance(error.messages, dict):
            first_field = next(iter(error.messages.values()), None)
            if isinstance(first_field, list) and first_field:
                message = str(first_field[0])
            elif first_field:
                message = str(first_field)
        elif error.messages:
            message = str(error.messages)
        return _json_error(message, 400)

    @app.errorhandler(404)
    def handle_404(_error):
        return _json_error("接口不存在", 404)

    @app.errorhandler(429)
    def handle_rate_limit(_error):
        return _json_error("请求过于频繁，请稍后再试", 429)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        app.logger.exception("Unhandled exception: %s", error)
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        return _json_error("服务器内部错误", status_code)
