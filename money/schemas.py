from marshmallow import Schema, fields, validate

from models import CategoryType


class CategorySchema(Schema):
    id = fields.Int(dump_only=True)
    description = fields.Str(required=True, validate=validate.Length(1, 255))
    type = fields.Str(validate=validate.OneOf([type.value for type in CategoryType]))


class TransactionSchema(Schema):
    id = fields.Int(dump_only=True)
    created_by_id = fields.Int(required=True, dump_only=True)
    category_id = fields.Int(required=True)
    category_name = fields.Method('get_category_name', dump_only=True)
    amount = fields.Decimal(required=True, validate=validate.Range(1, 1000000000))
    transaction_date = fields.DateTime(dump_only=True)
    description = fields.Str(required=False, validate=validate.Length(0, 255))

    def get_category_name(self, obj):
        return obj.category.description if obj.category else None
