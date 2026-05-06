from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import FUNPAY_URL, PM_USERNAME


def _pm_url() -> str | None:
    username = PM_USERNAME.strip().lstrip("@")
    if not username:
        return None
    return f"https://t.me/{username}"


inline_kb_start = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🧺 купить", callback_data="store")],
        [
            InlineKeyboardButton(text="👤 профиль", callback_data="profile"),
            InlineKeyboardButton(text="💬 поддержка", callback_data="support"),
        ],
    ]
)

inline_kb_back_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔙 назад", callback_data="back")]
    ]
)


def build_store_kb(products: list[tuple[int, str, int]]) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"{name} - {price} RUB",
                callback_data=f"product_{product_id}",
            )
        ]
        for product_id, name, price in products
    ]
    keyboard.append([InlineKeyboardButton(text="🔙 назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_product_buy_kb() -> InlineKeyboardMarkup:
    keyboard: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="🛒 FunPay", url=FUNPAY_URL)]
    ]

    pm_url = _pm_url()
    if pm_url:
        keyboard.append(
            [InlineKeyboardButton(text="✉️ Личные сообщения", url=pm_url)]
        )
    else:
        keyboard.append(
            [InlineKeyboardButton(text="✉️ Личные сообщения", callback_data="pm_info")]
        )

    keyboard.append([InlineKeyboardButton(text="🔙 к товарам", callback_data="store")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_support_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍️ написать в поддержку", callback_data="support_write")],
            [InlineKeyboardButton(text="🔙 назад", callback_data="back")],
        ]
    )
