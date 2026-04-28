from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from database.users import get_top_users, get_or_create_user

router = Router()

async def show_top(msg_or_cb, edit: bool = False, n: int = 10):
    users = await get_top_users(n)
    text = f"🏆 <b>Топ {n} пользователей</b>\n\n"
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    for i, u in enumerate(users, 1):
        medal = medals.get(i, f"{i}.")
        name = u.get('first_name') or u.get('username') or str(u['user_id'])
        text += f"{medal} {name} — {u['grams']:,} грамм\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ])
    if edit:
        await msg_or_cb.edit_text(text, reply_markup=kb)
    else:
        await msg_or_cb.answer(text)

@router.message(Command("топ"))
async def cmd_top(msg: Message):
    await get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
    parts = msg.text.strip().split()
    n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10
    n = min(n, 50)
    await show_top(msg, n=n)
