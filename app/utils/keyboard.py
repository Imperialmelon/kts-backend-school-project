import typing

from sqlalchemy import Sequence

from app.store.database.models import Asset

if typing.TYPE_CHECKING:
    from app.web.app import Application


def create_inline_keyboard(buttons: list[list[dict]]) -> dict:
    return {
        "inline_keyboard": [
            [
                {
                    "text": btn["text"],
                    "callback_data": btn.get("callback_data"),
                }
                for btn in row
            ]
            for row in buttons
        ]
    }


def get_participation_keyboard() -> dict:
    return create_inline_keyboard(
        [
            [
                {"text": "✅ Подтвердить", "callback_data": "confirm"},
                {"text": "❌ Отменить", "callback_data": "cancel"},
            ]
        ]
    )


async def get_available_stocks_keyboard(
    app: "Application", assets: Sequence[Asset], session_id: int
) -> dict:
    price = await app.game_accessor.get_asset_price(session_id, session_id)
    buttons = [
        [
            {
                "text": f"{asset.title}" f" - " f"{price}",
                "callback_data": f"buy_asset_{asset.id}_{session_id}",
            }
        ]
        for asset in assets
    ]
    return create_inline_keyboard(buttons)


def get_options_keyboard(player_id: int, session_id: int) -> dict:
    buttons = [
        [
            {
                "text": "Доступные активы",
                "callback_data": f"assets_available_{session_id}",
            },
            {"text": "Мои активы", "callback_data": f"assets_my_{player_id}"},
        ]
    ]
    return create_inline_keyboard(buttons)
