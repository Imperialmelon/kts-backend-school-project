import typing

from app.utils.keyboard import (
    get_available_stocks_keyboard,
    get_options_keyboard,
    get_participation_keyboard,
)

if typing.TYPE_CHECKING:
    from app.web.app import Application

from app.store.database.models import Asset, UserInGame


class GameMessanger:
    @staticmethod
    async def send_options_keyboard(
        app: "Application", chat_id: int, player_id: int, session_id: int
    ) -> typing.NoReturn:
        keyboard = get_options_keyboard(player_id, session_id)
        await app.tg_client.send_message(
            chat_id=chat_id,
            text="Выберите действие:",
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
        app: "Application", chat_id: int, players: list[UserInGame]
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
        app: "Application", chat_id: int, assets: list[tuple[Asset, int]]
    ) -> typing.NoReturn:
        message = "Ваши активы:\n" + "\n".join(
            f"{asset.title} - {quantity} шт." for asset, quantity in assets
        )

        await app.tg_client.send_message(chat_id=chat_id, text=message)

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
        app: "Application", chat_id: int
    ) -> typing.NoReturn:
        await app.tg_client.send_message(
            chat_id=chat_id,
            text="нет денег",
        )
