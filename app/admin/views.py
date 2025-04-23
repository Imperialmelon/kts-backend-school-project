from aiohttp.web_exceptions import HTTPForbidden
from aiohttp_apispec import (
    docs,
    querystring_schema,
    request_schema,
    response_schema,
)
from aiohttp_session import get_session, new_session

from app.admin.schemes import (
    AdminLoginSchema,
    AdminResponseSchema,
    AdminSchema,
    AssetCreateSchema,
    AssetResponseSchema,
    ChatIdSchema,
    GameInChatResponseSchema,
    GameResponseSchema,
    OkResponseSchema,
    PlayerSchema,
    TgUserSchema,
    TopPlayerSchema,
    TopPlayersSchema,
)
from app.web.app import View
from app.web.decorators import login_required
from app.web.utils import (
    check_admin_credentials,
    error_json_response,
    json_response,
)


class AdminLoginView(View):
    @docs(tags=["admin"], summary="Admin login")
    @request_schema(AdminLoginSchema)
    @response_schema(AdminResponseSchema, 200)
    async def post(self):
        email = self.data["email"]
        admin = await self.store.admin_accessor.get_by_email(email=email)
        if not check_admin_credentials(
            admin=admin, password=self.data["password"]
        ):
            raise HTTPForbidden(reason="Invalid credentials")
        session = await new_session(self.request)
        session["admin_email"] = email
        return json_response(data=AdminSchema().dump(admin))


class AdminLogoutView(View):
    @docs(tags=["admin"], summary="Admin logout")
    @response_schema(OkResponseSchema, 200)
    @login_required
    async def delete(self):
        session = await get_session(self.request)
        if "admin_email" in session:
            del session["admin_email"]
        return json_response(data={})


class CheckGamesView(View):
    @docs(
        tags=["statistics"],
        summary="Get games in chat",
        description="Returns all games in specified chat with players",
    )
    @querystring_schema(ChatIdSchema)
    @response_schema(GameInChatResponseSchema, 200)
    @login_required
    async def get(self):
        chat_id = int(self.request.query.get("chat_id"))

        chat = await self.store.telegram_accessor.get_chat_by_telegram_id(
            chat_id
        )
        if not chat:
            return error_json_response(
                http_status=404, message="Chat not found"
            )

        games = await self.store.game_accessor.get_games_in_chat(chat.id)

        result = {"chat_id": chat_id, "games": []}

        for game in games:
            players_data = []

            for player in game.player_associations:
                player_data = PlayerSchema().dump(
                    {
                        "id": player.id,
                        "state": player.state,
                        "cur_balance": player.cur_balance,
                        "user": TgUserSchema().dump(player.user),
                    }
                )
                players_data.append(player_data)

            winner_data = (
                TgUserSchema().dump(game.winner) if game.winner else None
            )
            game_data = GameResponseSchema().dump(
                {
                    "id": game.id,
                    "started_at": game.started_at,
                    "finished_at": game.finished_at,
                    "state": game.state,
                    "start_player_balance": game.start_player_balance,
                    "session_limit": game.session_limit,
                    "players": players_data,
                    "winner": winner_data,
                }
            )

            result["games"].append(game_data)

        return json_response(result)


class TopPlayersView(View):
    @docs(
        tags=["statistics"],
        summary="Get top players",
        description="Returns the top of players",
    )
    @response_schema(TopPlayersSchema, 200)
    @login_required
    async def get(self):
        data = await self.store.game_accessor.get_top_players()
        top_players = []
        for player, win_cnt, games_played_cnt in data:
            top_player = TopPlayerSchema().dump(
                {
                    "id": player.id,
                    "first_name": player.first_name,
                    "win_cnt": win_cnt,
                    "games_played_cnt": games_played_cnt,
                }
            )
            top_players.append(top_player)
        return json_response(
            data=TopPlayersSchema().dump({"players": top_players})
        )


class CreateAssetView(View):
    @docs(
        tags=["admin"],
        summary="Create asset",
        description="Creates a new asset",
    )
    @request_schema(AssetCreateSchema)
    @response_schema(AssetResponseSchema, 200)
    @login_required
    async def post(self):
        asset_title = self.data["title"]
        asset = await self.store.game_accessor.create_asset(asset_title)
        return json_response(data=AssetResponseSchema().dump(asset))
