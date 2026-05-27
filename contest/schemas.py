from marshmallow import Schema, fields, validate


class RegisterSchema(Schema):
    code = fields.Str(required=True)
    messenger_id = fields.Str(required=True)
    display_name = fields.Str(load_default='')


class UpdateStatusSchema(Schema):
    code = fields.Str(required=True)
    status = fields.Str(required=True, validate=validate.OneOf(['active', 'inactive']))
