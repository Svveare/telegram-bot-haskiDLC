import html

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from filters.admin_filter import AdminFilter
from keyboards.admin_kb import admin_kb, support_admin_kb, products_admin_kb
from keyboards.inline import inline_kb_start
from databases.queries import (
    add_product,
    get_products,
    get_product,
    delete_product,
    update_product_price,
    get_all_user_ids,
    get_open_support_ticket_ids,
    get_support_ticket,
    ignore_support_ticket,
    answer_support_ticket,
)
from states.admin_states import AddProduct, EditProduct, BroadcastMessage, SupportReply

admin_router = Router(name="admin")
admin_router.message.filter(AdminFilter())
admin_router.callback_query.filter(AdminFilter())


def _build_products_manage_kb(action_prefix: str, products: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text=name, callback_data=f"{action_prefix}_{product_id}")]
        for product_id, name in products
    ]
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="products_admin")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def _build_support_ticket_kb(ticket_id: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    nav_row = [
        InlineKeyboardButton(
            text="⬅️",
            callback_data=f"support_prev_{ticket_id}" if has_prev else "support_noop",
        ),
        InlineKeyboardButton(
            text="➡️",
            callback_data=f"support_next_{ticket_id}" if has_next else "support_noop",
        ),
    ]
    action_row = [
        InlineKeyboardButton(text="✉️ Ответить", callback_data=f"support_reply_{ticket_id}"),
        InlineKeyboardButton(text="🗑 Игнор", callback_data=f"support_ignore_{ticket_id}"),
    ]
    back_row = [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")]
    return InlineKeyboardMarkup(inline_keyboard=[nav_row, action_row, back_row])


def _parse_positive_int(value: str) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed


def _message_text(message: Message) -> str:
    return (message.text or "").strip()


def _support_queue_position(ticket_id: int, open_ids: list[int]) -> tuple[int, int]:
    if not open_ids:
        return 0, 0
    try:
        index = open_ids.index(ticket_id)
    except ValueError:
        index = 0
    return index + 1, len(open_ids)


def _format_support_ticket(ticket: tuple[int, int, str | None, str | None, str, str, str], position: int, total: int) -> str:
    ticket_id, user_id, username, full_name, user_message, _status, created_at = ticket
    title = full_name or "Без имени"
    username_line = f"@{username}" if username else "не указан"
    return (
        f"🎧 Обращение {position}/{total}\n\n"
        f"ID: #{ticket_id}\n"
        f"Пользователь: {html.escape(title)}\n"
        f"Username: {html.escape(username_line)}\n"
        f"User ID: <code>{user_id}</code>\n"
        f"Создано: {created_at}\n\n"
        f"Сообщение:\n{html.escape(user_message)}"
    )


def _select_neighbor_ticket_id(current_id: int, direction: int) -> int | None:
    open_ids = get_open_support_ticket_ids()
    if not open_ids:
        return None
    try:
        index = open_ids.index(current_id)
    except ValueError:
        return open_ids[0]

    new_index = index + direction
    if new_index < 0:
        new_index = 0
    if new_index >= len(open_ids):
        new_index = len(open_ids) - 1
    return open_ids[new_index]


async def _show_support_ticket(callback: CallbackQuery, ticket_id: int) -> None:
    open_ids = get_open_support_ticket_ids()
    if not open_ids:
        await callback.message.edit_text(
            "🎧 В очереди поддержки нет открытых обращений.",
            reply_markup=support_admin_kb,
        )
        return

    ticket = get_support_ticket(ticket_id)
    if not ticket or ticket[5] != "open":
        actual_id = open_ids[0]
        ticket = get_support_ticket(actual_id)
        ticket_id = actual_id

    if not ticket:
        await callback.message.edit_text(
            "🎧 В очереди поддержки нет открытых обращений.",
            reply_markup=support_admin_kb,
        )
        return

    position, total = _support_queue_position(ticket_id, open_ids)
    has_prev = position > 1
    has_next = position < total
    await callback.message.edit_text(
        _format_support_ticket(ticket, position, total),
        parse_mode="HTML",
        reply_markup=_build_support_ticket_kb(ticket_id, has_prev, has_next),
    )


async def _send_next_support_ticket_to_admin(message: Message) -> None:
    open_ids = get_open_support_ticket_ids()
    if not open_ids:
        await message.answer("🎧 В очереди поддержки нет открытых обращений.")
        return

    ticket = get_support_ticket(open_ids[0])
    if not ticket:
        await message.answer("🎧 В очереди поддержки нет открытых обращений.")
        return

    position, total = _support_queue_position(open_ids[0], open_ids)
    has_prev = position > 1
    has_next = position < total
    await message.answer(
        _format_support_ticket(ticket, position, total),
        parse_mode="HTML",
        reply_markup=_build_support_ticket_kb(open_ids[0], has_prev, has_next),
    )


@admin_router.message(Command("admin"))
async def show_admin_panel(message: Message):
    await message.answer(
        "🔐 Админ-панель\n\nВыберите действие:",
        reply_markup=admin_kb,
    )


@admin_router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🔐 Админ-панель\n\nВыберите действие:",
        reply_markup=admin_kb,
    )
    await callback.answer()


@admin_router.callback_query(F.data == "close_admin")
async def close_admin_panel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "👋 Приветствуем!\n\nВыберите действие:",
        reply_markup=inline_kb_start,
    )
    await callback.answer()


@admin_router.callback_query(F.data == "support_noop")
async def support_noop(callback: CallbackQuery):
    await callback.answer()


@admin_router.callback_query(F.data == "support_admin")
async def show_support_admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    open_ids = get_open_support_ticket_ids()
    if not open_ids:
        await callback.message.edit_text(
            "🎧 В очереди поддержки нет открытых обращений.",
            reply_markup=support_admin_kb,
        )
        await callback.answer()
        return

    await _show_support_ticket(callback, open_ids[0])
    await callback.answer()


@admin_router.callback_query(F.data.startswith("support_prev_"))
async def support_prev(callback: CallbackQuery):
    try:
        ticket_id = int(callback.data.split("_", maxsplit=2)[2])
    except (IndexError, ValueError):
        await callback.answer()
        return

    next_id = _select_neighbor_ticket_id(ticket_id, direction=-1)
    if next_id is None:
        await callback.answer()
        return

    await _show_support_ticket(callback, next_id)
    await callback.answer()


@admin_router.callback_query(F.data.startswith("support_next_"))
async def support_next(callback: CallbackQuery):
    try:
        ticket_id = int(callback.data.split("_", maxsplit=2)[2])
    except (IndexError, ValueError):
        await callback.answer()
        return

    next_id = _select_neighbor_ticket_id(ticket_id, direction=1)
    if next_id is None:
        await callback.answer()
        return

    await _show_support_ticket(callback, next_id)
    await callback.answer()


@admin_router.callback_query(F.data.startswith("support_ignore_"))
async def support_ignore(callback: CallbackQuery):
    try:
        ticket_id = int(callback.data.split("_", maxsplit=2)[2])
    except (IndexError, ValueError):
        await callback.answer()
        return

    open_ids_before = get_open_support_ticket_ids()
    try:
        old_index = open_ids_before.index(ticket_id)
    except ValueError:
        old_index = 0

    ignore_support_ticket(ticket_id)
    open_ids_after = get_open_support_ticket_ids()
    if not open_ids_after:
        await callback.message.edit_text(
            "🎧 В очереди поддержки нет открытых обращений.",
            reply_markup=support_admin_kb,
        )
        await callback.answer("Обращение проигнорировано")
        return

    next_index = min(old_index, len(open_ids_after) - 1)
    await _show_support_ticket(callback, open_ids_after[next_index])
    await callback.answer("Обращение проигнорировано")


@admin_router.callback_query(F.data.startswith("support_reply_"))
async def support_reply_start(callback: CallbackQuery, state: FSMContext):
    try:
        ticket_id = int(callback.data.split("_", maxsplit=2)[2])
    except (IndexError, ValueError):
        await callback.answer()
        return

    ticket = get_support_ticket(ticket_id)
    if not ticket or ticket[5] != "open":
        await callback.answer("Обращение уже обработано", show_alert=True)
        return

    await state.update_data(ticket_id=ticket_id)
    await state.set_state(SupportReply.text)
    await callback.message.answer(
        f"Введите ответ для обращения #{ticket_id}:"
    )
    await callback.answer()


@admin_router.message(SupportReply.text)
async def support_reply_send(message: Message, state: FSMContext):
    reply_text = _message_text(message)
    if not reply_text:
        await message.answer("Введите текст ответа:")
        return

    data = await state.get_data()
    ticket_id = data.get("ticket_id")
    if not ticket_id:
        await message.answer("Не удалось определить обращение.")
        await state.clear()
        return

    ticket = get_support_ticket(ticket_id)
    if not ticket or ticket[5] != "open":
        await message.answer("Это обращение уже обработано.")
        await state.clear()
        return

    _id, user_id, _username, _full_name, user_message, _status, _created_at = ticket
    text_for_user = (
        "Ответ поддержки Haski Client на ваше сообщение:\n\n"
        f"{user_message}\n\n"
        f"{reply_text}"
    )

    try:
        await message.bot.send_message(user_id, text_for_user)
    except Exception:
        await message.answer(
            "Не удалось отправить ответ пользователю. Обращение осталось в очереди."
        )
        await state.clear()
        return

    answer_support_ticket(ticket_id, reply_text)
    await message.answer(f"✅ Ответ отправлен по обращению #{ticket_id}.")
    await state.clear()
    await _send_next_support_ticket_to_admin(message)


@admin_router.callback_query(F.data == "products_admin")
async def show_products_admin(callback: CallbackQuery):
    await callback.message.edit_text(
        "🧺 Управление товарами",
        reply_markup=products_admin_kb,
    )
    await callback.answer()


@admin_router.callback_query(F.data == "add_product")
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddProduct.name)
    await callback.message.answer("Введите название товара:")
    await callback.answer()


@admin_router.message(AddProduct.name)
async def add_product_name(message: Message, state: FSMContext):
    name = _message_text(message)
    if not name:
        await message.answer("Введите название товара:")
        return

    await state.update_data(name=name)
    await state.set_state(AddProduct.price)
    await message.answer("Введите цену:")


@admin_router.message(AddProduct.price)
async def add_product_price(message: Message, state: FSMContext):
    price = _parse_positive_int(_message_text(message))
    if price is None:
        await message.answer("Введите цену:")
        return

    await state.update_data(price=price)
    await state.set_state(AddProduct.description)
    await message.answer("Введите описание:")


@admin_router.message(AddProduct.description)
async def add_product_description(message: Message, state: FSMContext):
    description = _message_text(message)
    if not description:
        await message.answer("Введите описание:")
        return

    data = await state.get_data()
    add_product(
        name=data["name"],
        price=data["price"],
        description=description,
    )
    await message.answer("✅ Товар добавлен")
    await state.clear()


@admin_router.callback_query(F.data == "delete_product")
async def delete_product_menu(callback: CallbackQuery):
    products = get_products()
    if not products:
        await callback.message.edit_text(
            "Список товаров пуст.",
            reply_markup=products_admin_kb,
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "Выберите товар для удаления:",
        reply_markup=_build_products_manage_kb("delete_item", products),
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("delete_item_"))
async def delete_product_confirm(callback: CallbackQuery):
    try:
        product_id = int(callback.data.split("_", maxsplit=2)[2])
    except (IndexError, ValueError):
        await callback.answer()
        return

    if not get_product(product_id):
        await callback.answer("Товар не найден", show_alert=True)
        return

    delete_product(product_id)
    await callback.answer("Удалено ✅")
    await callback.message.edit_text("Товар удалён", reply_markup=products_admin_kb)


@admin_router.callback_query(F.data == "edit_product")
async def edit_product_menu(callback: CallbackQuery):
    products = get_products()
    if not products:
        await callback.message.edit_text(
            "Список товаров пуст.",
            reply_markup=products_admin_kb,
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "Выберите товар:",
        reply_markup=_build_products_manage_kb("edit_item", products),
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("edit_item_"))
async def edit_product_start(callback: CallbackQuery, state: FSMContext):
    try:
        product_id = int(callback.data.split("_", maxsplit=2)[2])
    except (IndexError, ValueError):
        await callback.answer()
        return

    if not get_product(product_id):
        await callback.answer("Товар не найден", show_alert=True)
        return

    await state.update_data(product_id=product_id)
    await state.set_state(EditProduct.new_price)
    await callback.message.answer("Введите новую цену:")
    await callback.answer()


@admin_router.message(EditProduct.new_price)
async def edit_product_price(message: Message, state: FSMContext):
    new_price = _parse_positive_int(_message_text(message))
    if new_price is None:
        await message.answer("Введите новую цену:")
        return

    data = await state.get_data()
    update_product_price(data["product_id"], new_price)

    await message.answer("✅ Цена обновлена")
    await state.clear()


@admin_router.callback_query(F.data == "broadcast_admin")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastMessage.text)
    await callback.message.answer("Введите текст рассылки:")
    await callback.answer()


@admin_router.message(BroadcastMessage.text)
async def send_broadcast(message: Message, state: FSMContext):
    text = _message_text(message)
    if not text:
        await message.answer("Введите текст рассылки:")
        return

    user_ids = get_all_user_ids()
    if not user_ids:
        await message.answer("Нет пользователей для рассылки.")
        await state.clear()
        return

    success = 0
    failed = 0
    for user_id in user_ids:
        try:
            await message.bot.send_message(user_id, text)
            success += 1
        except Exception:
            failed += 1

    await message.answer(
        f"Рассылка завершена.\nДоставлено: {success}\nОшибок: {failed}"
    )
    await state.clear()
