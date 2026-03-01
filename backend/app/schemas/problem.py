"""Problem request schemas."""

from marshmallow import Schema, ValidationError, fields, validate, validates


class RecognizeSchema(Schema):
    image = fields.String(required=True, error_messages={"required": "缺少图片数据"})


class ParseSchema(Schema):
    text = fields.String(required=True, error_messages={"required": "缺少题目文本"})

    @validates("text")
    def validate_text(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("缺少题目文本")


class SolveSchema(Schema):
    text = fields.String(required=True, error_messages={"required": "缺少题目文本"})
    parse_result = fields.Dict(
        required=True,
        data_key="parseResult",
        error_messages={"required": "缺少解析结果"},
    )

    @validates("text")
    def validate_text(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("缺少题目文本")


class SolveProblemSchema(Schema):
    type = fields.String(
        required=True,
        validate=validate.OneOf(["text", "image"], error="无效的输入类型"),
        error_messages={"required": "缺少必要参数"},
    )
    content = fields.Raw(required=True, error_messages={"required": "缺少必要参数"})


class SolveStreamSchema(Schema):
    text = fields.String(required=True, error_messages={"required": "缺少必要参数"})
    parse_result = fields.Dict(
        required=True,
        data_key="parseResult",
        error_messages={"required": "缺少必要参数"},
    )

    @validates("text")
    def validate_text(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("缺少必要参数")
