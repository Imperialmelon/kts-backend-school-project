import typing

from sqlalchemy import Sequence

from app.utils.keyboard import (
    get_available_stocks_keyboard,
    get_options_keyboard,
    get_participation_keyboard,
    get_player_assets_keyboard,
    get_selling_keyboard,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application

from app.store.database.models import Asset, UserInGame


class GameMessenger:
    @staticmethod
    async def send_options_keyboard(
        app: "Application", chat_id: int, player_id: int, session_id: int
    ) -> typing.NoReturn:
        user = await app.telegram_accessor.get_user_by_custom_id(player_id)
        keyboard = get_options_keyboard(player_id, session_id)
        await app.tg_client.send_message(
            chat_id=chat_id,
            text=f"{user.first_name}, выберите действие:",
            reply_markup=keyboard,
        )

    @staticmethod
    async def send_available_stocks_keyboard(
        app: "Application",
        chat_id: int,
        session_id: int,
        assets: typing.Sequence[typing.Any],
    ) -> typing.NoReturn:
        keyboard = await get_available_stocks_keyboard(app, assets, session_id)
        await app.tg_client.send_message(
            chat_id=chat_id,
            text="Доступные активы:",
            reply_markup=keyboard,
        )

    @staticmethod
    async def send_participation_keyboard(
        app: "Application", chat_id: int
    ) -> typing.NoReturn:
        keyboard = get_participation_keyboard()
        await app.tg_client.send_message(
            chat_id=chat_id,
            text="Подтвердите участие:",
            reply_markup=keyboard,
        )

    @staticmethod
    async def session_start_informer(
        app: "Application", chat_id: int, session_num: int, game_id: int
    ) -> None:
        player_associations = await app.game_accessor.get_game_active_players(
            game_id
        )

        players_list = "\n".join(
            f"• {user.first_name}: {player.cur_balance}"
            for player, user in player_associations
        )

        await app.tg_client.send_message(
            chat_id=chat_id,
            text=(
                f"*Сессия {session_num} начата!*\n\n"
                f"Участники и их балансы:\n"
                f"{players_list}"
            ),
        )

    @staticmethod
    async def unknown_command_message(
        app: "Application", chat_id: int
    ) -> typing.NoReturn:
        await app.tg_client.send_message(
            chat_id=chat_id,
            text="Неизвестная команда",
        )

    @staticmethod
    async def successful_purchase_message(
        app: "Application", chat_id: int, asset_title: str, player_name: str
    ) -> typing.NoReturn:
        await app.tg_client.send_message(
            chat_id=chat_id,
            text=f"Игрок {player_name} приобрел {asset_title}",
        )

    @staticmethod
    async def players_list_message(
        app: "Application", chat_id: int, players: Sequence[UserInGame]
    ) -> typing.NoReturn:
        player_list = "\n".join(
            [f"• {player.first_name}" for player in players]
        )
        await app.tg_client.send_message(
            chat_id=chat_id,
            text=f"Текущие игроки:\n{player_list}",
        )

    @staticmethod
    async def not_enough_players_message(
        app: "Application", chat_id: int
    ) -> typing.NoReturn:
        await app.tg_client.send_message(
            chat_id=chat_id,
            text="Недостаточно игроков для игры",
        )

    @staticmethod
    async def successful_participation_message(
        app: "Application", chat_id: int, player_name: str
    ) -> typing.NoReturn:
        await app.tg_client.send_message(
            chat_id=chat_id,
            text=f"Пользователь {player_name} подтвердил участие",
        )

    @staticmethod
    async def player_already_participating_message(
        app: "Application", chat_id: int, player_name: str
    ) -> typing.NoReturn:
        await app.tg_client.send_message(
            chat_id=chat_id,
            text=f"{player_name}, ваше участие уже подтверждено",
        )

    @staticmethod
    async def cancel_participation_message(
        app: "Application", chat_id: int, player_name: str
    ) -> typing.NoReturn:
        await app.tg_client.send_message(
            chat_id=chat_id,
            text=f"Пользователь {player_name} отменил участие",
        )

    @staticmethod
    async def no_available_assets_message(
        app: "Application", chat_id: int
    ) -> typing.NoReturn:
        await app.tg_client.send_message(
            chat_id=chat_id,
            text="Нет доступных активов",
        )

    @staticmethod
    async def no_player_found_message(
        app: "Application", chat_id: int
    ) -> typing.NoReturn:
        await app.tg_client.send_message(
            chat_id=chat_id, text="Игрок не найден"
        )

    @staticmethod
    async def player_has_no_assets_message(
        app: "Application", chat_id: int
    ) -> typing.NoReturn:
        await app.tg_client.send_message(
            chat_id=chat_id, text="У вас пока нет активов"
        )

    @staticmethod
    async def player_assets_message(
        app: "Application",
        chat_id: int,
        assets: list[tuple[Asset, int]],
        session_id: int,
        player_id: int,
    ) -> typing.NoReturn:
        user = await app.telegram_accessor.get_user_by_custom_id(player_id)
        keyboard = get_player_assets_keyboard(assets, session_id)

        await app.tg_client.send_message(
            chat_id=chat_id,
            text=f"{user.first_name}, ваши активы:",
            reply_markup=keyboard,
        )

    @staticmethod
    async def selling_menu_message(
        app: "Application",
        chat_id: int,
        asset: Asset,
        session_id: int,
        user_id: int,
        price: int,
    ) -> typing.NoReturn:
        keyboard = get_selling_keyboard(user_id, asset.id, session_id)

        await app.tg_client.send_message(
            chat_id=chat_id,
            text=f"{asset.title}\nТекущая цена: {price}",
            reply_markup=keyboard,
        )

    @staticmethod
    async def game_over_message(
        app: "Application", chat_id: int
    ) -> typing.NoReturn:
        await app.store.tg_api.tg_client.send_message(
            chat_id=chat_id,
            text="Игра окончена",
        )

    @staticmethod
    async def starting_timer_message(
        app: "Application", chat_id: int
    ) -> typing.NoReturn:
        await app.tg_client.send_message(
            chat_id=chat_id,
            text="Игра началась! Таймер запущен",
        )

    @staticmethod
    async def game_already_going_message(
        app: "Application", chat_id: int
    ) -> typing.NoReturn:
        await app.tg_client.send_message(
            chat_id=chat_id,
            text="Игра уже начата",
        )

    @staticmethod
    async def insufficient_funds_message(
        app: "Application", chat_id: int, player_id: int
    ) -> typing.NoReturn:
        user = await app.game_accessor.get_user_by_player_id(player_id)
        await app.tg_client.send_message(
            chat_id=chat_id,
            text=f"{user.first_name}, у вас не хватает баланса для покупки",
        )

    @staticmethod
    async def not_your_assets_message(
        app: "Application", chat_id: int
    ) -> typing.NoReturn:
        await app.tg_client.send_message(
            chat_id=chat_id,
            text="Это не ваши активы",
        )

    @staticmethod
    async def successful_sale_message(
        app: "Application", chat_id: int, asset_title: str, player_name: str
    ) -> None:
        await app.tg_client.send_message(
            chat_id=chat_id,
            text=f"Игрок {player_name} продал {asset_title}",
        )

    @staticmethod
    async def no_active_for_sale_message(
        app: "Application", chat_id: int
    ) -> typing.NoReturn:
        await app.tg_client.send_message(
            chat_id=chat_id,
            text="Актив отсутствует",
        )
