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
    buttons = [
        [
            {
                "text": f"{asset.title}" f" - " f"{await app.game_accessor.get_asset_price(asset.id, session_id)}",
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


def get_player_assets_keyboard(
    assets: list[tuple[Asset, int]], session_id: int
) -> dict:
    buttons = [
        [
            {
                "text": f"{asset.title} - {quantity} шт.",
                "callback_data": f"asset_info_{asset.id}_{session_id}",
            }
        ]
        for asset, quantity in assets
    ]
    buttons.append(
        [{"text": "⬅️ Назад", "callback_data": f"assets_available_{session_id}"}]
    )
    return create_inline_keyboard(buttons)


def get_selling_keyboard(user_id: int, asset_id: int, session_id: int) -> dict:
    buttons = [
        [
            {
                "text": "💰 Продать",
                "callback_data": f"sell_asset_{asset_id}_{session_id}",
            },
            {"text": "⬅️ Назад", "callback_data": f"assets_my_{user_id}"},
        ]
    ]
    return create_inline_keyboard(buttons)
