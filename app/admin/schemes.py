from marshmallow import Schema, fields

from app.web.schemas import OkResponseSchema


class AdminLoginSchema(Schema):
    email = fields.Str(required=True)
    password = fields.Str(required=True)


class AdminSchema(Schema):
    id = fields.Int(required=True)
    email = fields.Str(required=True)


class AdminResponseSchema(OkResponseSchema):
    data = fields.Nested(AdminSchema)
