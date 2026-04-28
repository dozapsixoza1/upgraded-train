import random
from datetime import date
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from database.users import get_or_create_user, get_user, update_user, add_grams
from database.bosses import (
    get_active_boss_session, create_boss_session,
    apply_damage, get_boss_leaderboard
)
from database.db import get_db
from config import BOSSES, BOSS_DAILY_FREE_ATTACKS, BOSS_EXTRA_ATTACK_COST

router = Router()

def bosses_list_kb():
    buttons = []
    for boss in BOSSES:
        buttons.append([InlineKeyboardButton(
            text=f"{'⭐️'*min(boss['id'],3)} {boss['name']} (ур.{boss['min_level']}+)",
            callback_data=f"boss_info_{boss['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="menu_hogwarts")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def boss_action_kb(boss_id: int, session_id: int = None):
    buttons = [
        [InlineKeyboardButton(text="⚔️ Атаковать!", callback_data=f"boss_attack_{boss_id}_{session_id or 0}")],
        [InlineKeyboardButton(text="🔙 К боссам", callback_data="hogwarts_bosses")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.callback_query(F.data == "hogwarts_bosses")
async def cb_bosses_list(cb: CallbackQuery):
    await cb.message.edit_text("👹 <b>Боссы Хогвартса</b>\nВыберите босса:", reply_markup=bosses_list_kb())

@router.callback_query(F.data.startswith("boss_info_"))
async def cb_boss_info(cb: CallbackQuery):
    boss_id = int(cb.data.split("_")[2])
    boss = next(b for b in BOSSES if b["id"] == boss_id)
    user = await get_or_create_user(cb.from_user.id, cb.from_user.username, cb.from_user.first_name)

    session = await get_active_boss_session(cb.from_user.id, boss_id)
    hp_text = ""
    session_id = None
    if session:
        pct = int(session['current_hp'] / boss['hp'] * 100)
        hp_text = f"\n❤️ HP: {session['current_hp']:,} / {boss['hp']:,} ({pct}%)"
        session_id = session['id']

    level_ok = user['xp'] >= boss['min_level'] or boss['min_level'] == 1
    rings_ok = user['rings'] >= boss['rings_required']

    access = "✅ Доступен" if (level_ok and rings_ok) else "❌ Недоступен"
    rings_text = f"💍 Нужно колец: {boss['rings_required']} (у вас: {user['rings']})"

    text = (
        f"👹 <b>{boss['name']}</b>\n\n"
        f"❤️ HP: {boss['hp']:,}\n"
        f"🏆 Награда: +{boss['reward']:,} ⭐️\n"
        f"📊 Минимальный уровень: {boss['min_level']}\n"
        f"{rings_text}\n"
        f"Статус: {access}"
        f"{hp_text}"
    )

    if level_ok and rings_ok:
        await cb.message.edit_text(text, reply_markup=boss_action_kb(boss_id, session_id))
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"💰 Атаковать за {BOSS_EXTRA_ATTACK_COST:,} грамм", callback_data=f"boss_buy_attack_{boss_id}")],
            [InlineKeyboardButton(text="🔙 К боссам", callback_data="hogwarts_bosses")],
        ])
        await cb.message.edit_text(text, reply_markup=kb)

@router.callback_query(F.data.startswith("boss_attack_"))
async def cb_boss_attack(cb: CallbackQuery):
    parts = cb.data.split("_")
    boss_id = int(parts[2])
    session_id = int(parts[3])

    boss = next(b for b in BOSSES if b["id"] == boss_id)
    user = await get_user(cb.from_user.id)

    # Check daily attacks
    today = str(date.today())
    attacks_today = user['daily_attacks_count'] if user['daily_attacks_date'] == today else 0

    if attacks_today >= BOSS_DAILY_FREE_ATTACKS:
        # Offer to pay
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"💰 Купить атаку за {BOSS_EXTRA_ATTACK_COST:,} грамм",
                callback_data=f"boss_buy_attack_{boss_id}"
            )],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"boss_info_{boss_id}")],
        ])
        await cb.message.edit_text(
            f"⏳ Вы использовали все {BOSS_DAILY_FREE_ATTACKS} бесплатных атак сегодня!\n"
            f"Купите дополнительную атаку:",
            reply_markup=kb
        )
        return

    # Get or create session
    session = await get_active_boss_session(cb.from_user.id, boss_id)
    if not session:
        sid = await create_boss_session(cb.from_user.id, boss_id)
        async with await get_db() as db:
            db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
            async with db.execute("SELECT * FROM boss_sessions WHERE id=?", (sid,)) as cur:
                session = await cur.fetchone()

    # Calculate damage
    damage = random.randint(
        user['strength'] * 10 + user['agility'] * 5,
        user['strength'] * 20 + user['intellect'] * 10
    )
    # Skill bonus
    skill_bonus = user['skill_damage'] // 10000
    damage += skill_bonus

    new_hp, killed = await apply_damage(session['id'], cb.from_user.id, damage)

    # Update attack count
    new_count = attacks_today + 1
    await update_user(cb.from_user.id,
                      daily_attacks_date=today,
                      daily_attacks_count=new_count)

    if killed:
        # Reward
        await add_grams(cb.from_user.id, boss['reward'])
        await update_user(cb.from_user.id,
                          rings=user['rings'] + 1,
                          xp=user['xp'] + boss['reward'] // 10)

        board = await get_boss_leaderboard(session['id'])
        board_text = "\n".join(
            f"  {i+1}. {r['first_name']}: {r['total']:,} урона"
            for i, r in enumerate(board[:5])
        )
        await cb.message.edit_text(
            f"💀 <b>{boss['name']} повержен!</b>\n\n"
            f"⚔️ Ваш удар: {damage:,}\n"
            f"🏆 Награда: +{boss['reward']:,} ⭐️\n"
            f"💍 Кольцо получено!\n\n"
            f"📊 Топ участников рейда:\n{board_text}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👹 К боссам", callback_data="hogwarts_bosses")]
            ])
        )
    else:
        pct = int(new_hp / boss['hp'] * 100)
        await cb.message.edit_text(
            f"⚔️ <b>Удар по {boss['name']}!</b>\n\n"
            f"💥 Урон: {damage:,}\n"
            f"❤️ HP: {new_hp:,} / {boss['hp']:,} ({pct}%)\n"
            f"🗡 Атак сегодня: {new_count}/{BOSS_DAILY_FREE_ATTACKS}",
            reply_markup=boss_action_kb(boss_id, session['id'])
        )

@router.callback_query(F.data.startswith("boss_buy_attack_"))
async def cb_boss_buy_attack(cb: CallbackQuery):
    boss_id = int(cb.data.split("_")[3])
    user = await get_user(cb.from_user.id)

    if user['grams'] < BOSS_EXTRA_ATTACK_COST:
        await cb.answer(f"Недостаточно грамм! Нужно {BOSS_EXTRA_ATTACK_COST:,}", show_alert=True)
        return

    await update_user(cb.from_user.id, grams=user['grams'] - BOSS_EXTRA_ATTACK_COST)
    # Reset daily limit for one more attack
    await update_user(cb.from_user.id, daily_attacks_count=max(0, user['daily_attacks_count'] - 1))
    await cb.answer("✅ Атака куплена!")
    await cb_boss_attack(cb)
