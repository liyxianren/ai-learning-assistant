"""Flask extensions initialization."""

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from marshmallow import ValidationError
from marshmallow import Schema


db = SQLAlchemy()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    headers_enabled=True,
)
cors = CORS()


class MarshmallowCompat:
    """Lightweight compatibility layer used by this project."""

    Schema = Schema
    ValidationError = ValidationError


ma = MarshmallowCompat()
