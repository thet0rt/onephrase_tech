from marshmallow import Schema, fields, validate


class AddTagSchema(Schema):
    tag = fields.Str(required=True)
    customer_id = fields.Str(required=True)
    delete = fields.Bool(required=False)
