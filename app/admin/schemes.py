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


class TgUserSchema(Schema):
    id = fields.Int(required=True)
    telegram_id = fields.Int(required=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(allow_none=True)
    username = fields.Str(allow_none=True)


class PlayerSchema(Schema):
    id = fields.Int(required=True)
    state = fields.Str(required=True)
    cur_balance = fields.Int(required=True)
    user = fields.Nested(TgUserSchema, required=True)


class GameResponseSchema(Schema):
    id = fields.Int(required=True)
    started_at = fields.DateTime(required=True)
    finished_at = fields.DateTime(allow_none=True)
    state = fields.Str(required=True)
    start_player_balance = fields.Int(required=True)
    session_limit = fields.Int(required=True)
    players = fields.List(fields.Nested(PlayerSchema), required=True)
    winner = fields.Nested(TgUserSchema, allow_none=True)


class GameInChatResponseSchema(Schema):
    chat_id = fields.Int(required=True)
    games = fields.List(fields.Nested(GameResponseSchema), required=True)


class ChatIdSchema(Schema):
    chat_id = fields.Integer(
        required=True, description="ID чата для получения статистики"
    )


class TopPlayerSchema(Schema):
    id = fields.Int(required=True)
    first_name = fields.Str(required=True)
    win_cnt = fields.Int(required=True)
    games_played_cnt = fields.Int(required=True)


class TopPlayersSchema(Schema):
    players = fields.List(fields.Nested(TopPlayerSchema), required=True)


class AssetCreateSchema(Schema):
    title = fields.Str(required=True)


class AssetResponseSchema(Schema):
    id = fields.Int(required=True)
    title = fields.Str(required=True)
