"""Auth request schemas."""

from marshmallow import Schema, ValidationError, fields, validate, validates_schema


class RegisterSchema(Schema):
    username = fields.String(
        required=True,
        validate=validate.Length(min=3, max=20, error="用户名长度必须在 3-20 个字符之间"),
        error_messages={"required": "请填写所有必填字段"},
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=6, error="密码长度不能少于 6 个字符"),
        error_messages={"required": "请填写所有必填字段"},
    )
    confirm_password = fields.String(
        required=True,
        data_key="confirmPassword",
        error_messages={"required": "请填写所有必填字段"},
    )

    @validates_schema
    def validate_confirm_password(self, data, **kwargs):
        if data.get("password") != data.get("confirm_password"):
            raise ValidationError("两次输入的密码不一致", field_name="confirmPassword")


class LoginSchema(Schema):
    username = fields.String(required=True, error_messages={"required": "请填写用户名和密码"})
    password = fields.String(required=True, error_messages={"required": "请填写用户名和密码"})
