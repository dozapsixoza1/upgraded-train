import random
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from database.users import get_or_create_user, get_user, update_user
from database.bosses import log_duel
from database.db import get_db
from config import DUEL_COOLDOWN_MINUTES

router = Router()

def calc_power(user: dict) -> int:
    return user['strength'] * 3 + user['agility'] * 2 + user['intellect']

async def get_cooldown(user_id: int):
    async with get_db() as db:
        async with db.execute("SELECT last_duel FROM duel_cooldowns WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else None

async def set_cooldown(user_id: int):
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO duel_cooldowns (user_id, last_duel) VALUES (?,?)",
            (user_id, datetime.utcnow().isoformat())
        )
        await db.commit()

@router.message(F.text.lower() == "дуэль")
async def cmd_duel(msg: Message):
    # Determine target
    if msg.reply_to_message:
        target_user = msg.reply_to_message.from_user
        if target_user.is_bot or target_user.id == msg.from_user.id:
            await msg.reply("❌ Нельзя вызвать на дуэль себя или бота!")
            return
    else:
        await msg.reply("⚔️ Напишите <b>дуэль</b> в ответ на сообщение соперника!")
        return

    # Cooldown check
    last_duel = await get_cooldown(msg.from_user.id)
    if last_duel:
        elapsed = datetime.utcnow() - datetime.fromisoformat(last_duel)
        remaining = timedelta(minutes=DUEL_COOLDOWN_MINUTES) - elapsed
        if remaining.total_seconds() > 0:
            mins = int(remaining.total_seconds() // 60)
            secs = int(remaining.total_seconds() % 60)
            await msg.reply(f"⏳ Дуэль будет доступна через <b>{mins}м {secs}с</b>")
            return

    attacker = await get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
    defender = await get_or_create_user(target_user.id, target_user.username, target_user.first_name)

    atk_power = calc_power(attacker)
    def_power = calc_power(defender)

    text = (
        f"⚔️ <b>Дуэль!</b>\n\n"
        f"🔴 {msg.from_user.first_name}\n"
        f"  Сила: {attacker['strength']} | Ловкость: {attacker['agility']} | Интеллект: {attacker['intellect']}\n"
        f"  Мощь: <b>{atk_power}</b>\n\n"
        f"🔵 {target_user.first_name}\n"
        f"  Сила: {defender['strength']} | Ловкость: {defender['agility']} | Интеллект: {defender['intellect']}\n"
        f"  Мощь: <b>{def_power}</b>\n\n"
        f"Ваши шансы на победу: <b>{round(atk_power/(atk_power+def_power)*100)}%</b>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Атаковать!", callback_data=f"duel_attack_{msg.from_user.id}_{target_user.id}_{msg.chat.id}")],
        [InlineKeyboardButton(text="🏃 Пропустить", callback_data=f"duel_skip_{msg.from_user.id}")],
    ])
    await msg.reply(text, reply_markup=kb)

@router.callback_query(F.data.startswith("duel_attack_"))
async def cb_duel_attack(cb: CallbackQuery):
    parts = cb.data.split("_")
    attacker_id = int(parts[2])
    defender_id = int(parts[3])
    chat_id = int(parts[4])

    if cb.from_user.id != attacker_id:
        await cb.answer("Это не ваша дуэль!", show_alert=True)
        return

    attacker = await get_user(attacker_id)
    defender = await get_user(defender_id)

    atk_power = calc_power(attacker)
    def_power = calc_power(defender)
    total = atk_power + def_power

    winner_id = attacker_id if random.randint(1, total) <= atk_power else defender_id
    loser_id = defender_id if winner_id == attacker_id else attacker_id

    winner = attacker if winner_id == attacker_id else defender
    loser = defender if winner_id == attacker_id else attacker

    grams_won = random.randint(50, 300)
    galeons_won = random.randint(10, 50)

    # Transfer rewards
    if loser['grams'] >= grams_won:
        await update_user(loser_id, grams=loser['grams'] - grams_won)
        await update_user(winner_id, grams=winner['grams'] + grams_won)
    await update_user(winner_id, galeons=winner['galeons'] + galeons_won, xp=winner['xp'] + 10)

    await log_duel(attacker_id, defender_id, winner_id, grams_won, galeons_won, chat_id)
    await set_cooldown(attacker_id)

    winner_name = attacker.get('first_name') or 'Атакующий'
    loser_name = defender.get('first_name') or 'Защитник'
    if winner_id == defender_id:
        winner_name, loser_name = loser_name, winner_name

    await cb.message.edit_text(
        f"⚔️ <b>Результат дуэли!</b>\n\n"
        f"🏆 Победитель: <b>{winner_name}</b>\n"
        f"💀 Проигравший: {loser_name}\n\n"
        f"💰 Награда: +{grams_won:,} грамм\n"
        f"🟡 Галеоны: +{galeons_won}\n"
        f"⭐️ Опыт: +10 XP"
    )

@router.callback_query(F.data.startswith("duel_skip_"))
async def cb_duel_skip(cb: CallbackQuery):
    attacker_id = int(cb.data.split("_")[2])
    if cb.from_user.id != attacker_id:
        await cb.answer("Это не ваша дуэль!", show_alert=True)
        return
    await cb.message.edit_text("🏃 Вы отказались от дуэли. Ищите более слабого противника!")
