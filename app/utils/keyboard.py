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
    alias = app.game_accessor.get_asset_price
    buttons = [
        [
            {
                "text": f"{asset.title}"
                f" - "
                f"{await alias(asset.id, session_id)}",
                "callback_data": f"buy_asset:{asset.id}-{session_id}",
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
                "callback_data": f"assets_available:{session_id}",
            },
            {"text": "Мои активы", "callback_data": f"assets_my:{player_id}"},
        ]
    ]
    return create_inline_keyboard(buttons)


def get_player_assets_keyboard(
    assets: list[tuple[Asset, int]], session_id: int
) -> dict:
    buttons = [
        [
            {
                "text": f"{asset.title} - {quantity} шт.",
                "callback_data": f"asset_info:{asset.id}-{session_id}",
            }
        ]
        for asset, quantity in assets
    ]
    return create_inline_keyboard(buttons)


def get_selling_keyboard(asset_id: int, session_id: int) -> dict:
    buttons = [
        [
            {
                "text": "💰 Продать",
                "callback_data": f"sell_asset:{asset_id}-{session_id}",
            },
        ]
    ]
    return create_inline_keyboard(buttons)
