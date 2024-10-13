from marshmallow import Schema, fields, validate

from models import CategoryType


class CategorySchema(Schema):
    id = fields.Int(dump_only=True)
    description = fields.Str(required=True, validate=validate.Length(1, 255))
    type = fields.Str(validate=validate.OneOf([type.value for type in CategoryType]))
