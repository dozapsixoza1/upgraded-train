import random
from datetime import date, datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from database.users import get_or_create_user, get_user, update_user, add_grams, get_transfer_history
from database.bosses import get_duel_history

router = Router()

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Профиль", callback_data="menu_profile"),
         InlineKeyboardButton(text="⚔️ Хогвартс", callback_data="menu_hogwarts")],
        [InlineKeyboardButton(text="🏰 Клан", callback_data="menu_clan"),
         InlineKeyboardButton(text="🏆 Топ", callback_data="menu_top")],
        [InlineKeyboardButton(text="🛒 Магазин", callback_data="menu_shop")],
    ])

def hogwarts_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👹 Боссы", callback_data="hogwarts_bosses")],
        [InlineKeyboardButton(text="📖 История дуэлей", callback_data="hogwarts_duel_history")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")],
    ])

@router.message(Command("start"))
async def cmd_start(msg: Message):
    user = await get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
    await msg.answer(
        f"👋 Добро пожаловать в <b>Legit</b>, {msg.from_user.first_name}!\n\n"
        "⚡️ Участвуй в дуэлях, побеждай боссов, создавай кланы и зарабатывай граммы!\n\n"
        "Нажми <b>Меню</b> для начала.",
        reply_markup=main_menu_kb()
    )

@router.message(F.text.lower().in_({"меню", "menu"}))
async def cmd_menu(msg: Message):
    await get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
    await msg.answer("📋 <b>Главное меню</b>", reply_markup=main_menu_kb())

@router.message(F.text.lower().in_({"баланс", "б", "грамм"}))
async def cmd_balance(msg: Message):
    user = await get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
    clan_text = f"Клан ID: {user['clan_id']}" if user['clan_id'] else "Нет клана"
    await msg.answer(
        f"💰 <b>Баланс {msg.from_user.first_name}</b>\n\n"
        f"⚪️ Граммы: <b>{user['grams']:,}</b>\n"
        f"🟡 Галеоны: <b>{user['galeons']:,}</b>\n"
        f"🏰 {clan_text}"
    )

@router.message(Command("история"))
async def cmd_history(msg: Message):
    user = await get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
    transfers = await get_transfer_history(msg.from_user.id)
    duels = await get_duel_history(msg.chat.id)

    text = "📜 <b>История переводов</b>\n"
    if transfers:
        for t in transfers[:5]:
            direction = "➡️ Отправил" if t['from_id'] == msg.from_user.id else "⬅️ Получил"
            text += f"{direction} <b>{t['amount']:,}</b> грамм — {t['created_at'][:10]}\n"
    else:
        text += "Нет переводов\n"

    text += "\n⚔️ <b>История дуэлей в чате</b>\n"
    if duels:
        for d in duels[:5]:
            winner = d['attacker_name'] if d['winner_id'] == d['attacker_id'] else d['defender_name']
            text += f"🏆 {winner} победил (+{d['grams_won']} грамм) — {d['created_at'][:10]}\n"
    else:
        text += "Нет дуэлей"

    await msg.answer(text)

@router.message(Command("бонус"))
async def cmd_bonus(msg: Message):
    user = await get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
    if user['grams'] > 0:
        await msg.answer("❌ Бонус доступен только при нулевом балансе!")
        return

    today = str(date.today())
    if user['last_bonus'] == today:
        await msg.answer("⏳ Бонус уже получен сегодня. Возвращайся завтра!")
        return

    amount = random.randint(100, 1000)
    await add_grams(msg.from_user.id, amount)
    await update_user(msg.from_user.id, last_bonus=today)
    await msg.answer(f"🎁 Вы получили бонус: <b>{amount}</b> грамм!")

# Callback handlers
@router.callback_query(F.data == "back_main")
async def cb_back_main(cb: CallbackQuery):
    await cb.message.edit_text("📋 <b>Главное меню</b>", reply_markup=main_menu_kb())

@router.callback_query(F.data == "menu_hogwarts")
async def cb_hogwarts(cb: CallbackQuery):
    await cb.message.edit_text("⚡️ <b>Хогвартс</b>", reply_markup=hogwarts_menu_kb())

@router.callback_query(F.data == "menu_top")
async def cb_top(cb: CallbackQuery):
    from handlers.leaderboard import show_top
    await show_top(cb.message, edit=True)
