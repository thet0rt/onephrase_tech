from marshmallow import Schema, fields, ValidationError


class CoordinatesSchema(Schema):
    x = fields.Int(required=True)
    y = fields.Int(required=True)


class TextOverlaySchema(Schema):
    product = fields.Str(required=True)
    coordinates = fields.Nested(CoordinatesSchema, required=True)
    fontSize = fields.Int(required=True)
    textWidth = fields.Float(required=True)
    text_image_white = fields.Str(required=False)
    text_image_black = fields.Str(required=False)


class ImageRequestSchema(Schema):
    items = fields.List(fields.Nested(TextOverlaySchema), required=True)
    category_1 = fields.Str(required=True)
    category_2 = fields.Str(required=True)
    design_number = fields.Str(required=True)
    text = fields.Str(required=True)
