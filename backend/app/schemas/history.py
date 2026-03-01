"""History query schema."""

from marshmallow import Schema, fields, validate


class HistoryQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    limit = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))
