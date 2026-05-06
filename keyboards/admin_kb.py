from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


admin_kb = InlineKeyboardMarkup(
  inline_keyboard=[
    [
            InlineKeyboardButton(text="🧺 товары", callback_data="products_admin"),
            InlineKeyboardButton(text="📣 рассылка", callback_data="broadcast_admin"),
        ],
        [
            InlineKeyboardButton(text="🎧 обращения", callback_data="support_admin"),
            InlineKeyboardButton(text="❌ закрыть", callback_data="close_admin"),
    ],
  ]
)

products_admin_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ добавить", callback_data="add_product"),
            InlineKeyboardButton(text="✏️ редактировать", callback_data="edit_product"),
            InlineKeyboardButton(text="🗑 удалить", callback_data="delete_product"),
        ],
        [InlineKeyboardButton(text="🔙 назад", callback_data="back_to_admin")],
    ]
)

support_admin_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔙 назад", callback_data="back_to_admin")]
    ]
)
