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
