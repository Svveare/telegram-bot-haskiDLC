import html

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from config import PM_USERNAME
from keyboards.inline import (
    inline_kb_back_menu,
    inline_kb_start,
    build_store_kb,
    build_product_buy_kb,
    build_support_kb,
)
from databases.queries import (
    get_product,
    get_products_for_user,
    add_user,
    add_support_ticket,
)
from states.menu_states import SupportRequest

router = Router()


def _track_user_from_callback(callback: CallbackQuery) -> None:
    add_user(
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name,
    )


def _track_user_from_message(message: Message) -> None:
    add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    _track_user_from_callback(callback)
    await callback.answer()

    username = f"@{callback.from_user.username}" if callback.from_user.username else "не указан"
    await callback.message.edit_text(
        "👤 Профиль\n\n"
        f"Ник: {username}\n"
        "Баланс: -\n"
        "Подписка: -",
        reply_markup=inline_kb_back_menu,
    )


@router.callback_query(F.data == "store")
async def show_store(callback: CallbackQuery):
    _track_user_from_callback(callback)
    await callback.answer()

    products = get_products_for_user()
    if not products:
        await callback.message.edit_text(
            "Товары Haski Client\n\n"
            "Сейчас список товаров пуст. Попробуйте позже.",
            reply_markup=inline_kb_back_menu,
        )
        return

    await callback.message.edit_text(
        "Товары Haski Client\n\n"
        "Ниже выберите нужный вариант подписки 👇",
        reply_markup=build_store_kb(products),
    )


@router.callback_query(F.data.startswith("product_"))
async def show_product(callback: CallbackQuery):
    _track_user_from_callback(callback)
    await callback.answer()

    try:
        product_id = int(callback.data.split("_", maxsplit=1)[1])
    except (IndexError, ValueError):
        return

    product = get_product(product_id)
    if not product:
        await callback.message.edit_text(
            "Товар не найден или уже удалён.",
            reply_markup=inline_kb_back_menu,
        )
        return

    name, price, description = product
    await callback.message.edit_text(
        "🧺 <b>{name}</b>\n\n"
        "💸 Цена: <b>{price} RUB</b>\n\n"
        "📝 Описание:\n{description}\n\n"
        "Выберите способ покупки:".format(
            name=html.escape(name),
            price=price,
            description=html.escape(description),
        ),
        parse_mode="HTML",
        reply_markup=build_product_buy_kb(),
    )


@router.callback_query(F.data == "pm_info")
async def show_pm_info(callback: CallbackQuery):
    username = PM_USERNAME.strip()
    if username:
        normalized = username if username.startswith("@") else f"@{username}"
        await callback.answer(
            f"Напишите в личные сообщения: {normalized}",
            show_alert=True,
        )
        return

    await callback.answer(
        "Юзернейм для личных сообщений пока не настроен.",
        show_alert=True,
    )


@router.callback_query(F.data == "support")
async def show_support(callback: CallbackQuery):
    _track_user_from_callback(callback)
    await callback.answer()

    await callback.message.edit_text(
        "💬 Поддержка Haski Client\n\n"
        "Нажмите кнопку ниже и отправьте сообщение одним текстом.",
        reply_markup=build_support_kb(),
    )


@router.callback_query(F.data == "support_write")
async def start_support_request(callback: CallbackQuery, state: FSMContext):
    _track_user_from_callback(callback)
    await state.set_state(SupportRequest.text)
    await callback.message.answer("Введите сообщение для поддержки:")
    await callback.answer()


@router.message(SupportRequest.text)
async def submit_support_request(message: Message, state: FSMContext):
    _track_user_from_message(message)
    text = (message.text or "").strip()
    if not text:
        await message.answer("Введите сообщение для поддержки:")
        return

    ticket_id = add_support_ticket(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        message=text,
    )
    await message.answer(
        f"✅ Ваше сообщение отправлено в поддержку.\nНомер обращения: #{ticket_id}",
        reply_markup=inline_kb_back_menu,
    )
    await state.clear()


@router.callback_query(F.data == "back")
async def back_to_start(callback: CallbackQuery, state: FSMContext):
    _track_user_from_callback(callback)
    await state.clear()
    await callback.answer()

    await callback.message.edit_text(
        "👋 Приветствуем! Вы перешли в Telegram-бот Haski Client.\n\n"
        "Для продолжения выберите кнопку ниже 👇",
        reply_markup=inline_kb_start,
    )
