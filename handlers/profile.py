from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from database.users import get_or_create_user, get_user, update_user, add_grams
from config import LEVEL_UPGRADE_COSTS, TRANSFER_LIMITS

router = Router()

def profile_kb(user):
    buttons = []
    next_level = user['account_level'] + 1
    if next_level <= 5:
        cost = LEVEL_UPGRADE_COSTS.get(next_level)
        buttons.append([InlineKeyboardButton(
            text=f"⬆️ Повысить уровень ({cost:,} грамм)",
            callback_data=f"upgrade_level_{next_level}"
        )])
    buttons.append([InlineKeyboardButton(text="📊 Прокачать характеристики", callback_data="upgrade_stats")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def format_profile(user, name: str) -> str:
    limit = TRANSFER_LIMITS[user['account_level']]
    limit_str = "безлимит" if limit is None else f"{limit:,}"
    clan_str = f"#{user['clan_id']}" if user['clan_id'] else "Нет клана"
    return (
        f"👤 <b>Профиль {name}</b>\n\n"
        f"🆔 ID: <code>{user['user_id']}</code>\n"
        f"⭐️ Уровень: <b>{user['xp']}</b> XP\n"
        f"🔰 Аккаунт: <b>{user['account_level']} уровень</b>\n\n"
        f"💰 Граммы: <b>{user['grams']:,}</b>\n"
        f"🟡 Галеоны: <b>{user['galeons']:,}</b>\n"
        f"💍 Кольца: <b>{user['rings']}</b>\n\n"
        f"⚔️ Сила: <b>{user['strength']}</b>\n"
        f"🏃 Ловкость: <b>{user['agility']}</b>\n"
        f"🧠 Интеллект: <b>{user['intellect']}</b>\n\n"
        f"🏰 Клан: <b>{clan_str}</b>\n"
        f"📤 Лимит передачи: <b>{limit_str}</b> грамм/сутки"
    )

@router.message(Command("профиль"))
async def cmd_profile(msg: Message):
    user = await get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
    await msg.answer(format_profile(user, msg.from_user.first_name), reply_markup=profile_kb(user))

@router.callback_query(F.data == "menu_profile")
async def cb_profile(cb: CallbackQuery):
    user = await get_or_create_user(cb.from_user.id, cb.from_user.username, cb.from_user.first_name)
    await cb.message.edit_text(format_profile(user, cb.from_user.first_name), reply_markup=profile_kb(user))

@router.callback_query(F.data.startswith("upgrade_level_"))
async def cb_upgrade_level(cb: CallbackQuery):
    new_level = int(cb.data.split("_")[-1])
    user = await get_user(cb.from_user.id)
    cost = LEVEL_UPGRADE_COSTS.get(new_level)

    if not cost:
        await cb.answer("Уже максимальный уровень!", show_alert=True)
        return
    if user['account_level'] >= new_level:
        await cb.answer("Уровень уже достигнут!", show_alert=True)
        return
    if user['grams'] < cost:
        await cb.answer(f"Недостаточно грамм! Нужно {cost:,}", show_alert=True)
        return

    await update_user(cb.from_user.id, grams=user['grams'] - cost, account_level=new_level)
    user = await get_user(cb.from_user.id)
    await cb.message.edit_text(format_profile(user, cb.from_user.first_name), reply_markup=profile_kb(user))
    await cb.answer(f"✅ Уровень повышен до {new_level}!")

@router.callback_query(F.data == "upgrade_stats")
async def cb_upgrade_stats(cb: CallbackQuery):
    user = await get_user(cb.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⚔️ Сила +1 (100 галеонов)", callback_data="stat_strength")],
        [InlineKeyboardButton(text=f"🏃 Ловкость +1 (100 галеонов)", callback_data="stat_agility")],
        [InlineKeyboardButton(text=f"🧠 Интеллект +1 (100 галеонов)", callback_data="stat_intellect")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_profile")],
    ])
    await cb.message.edit_text(
        f"📊 <b>Прокачка характеристик</b>\n"
        f"🟡 Галеоны: {user['galeons']:,}\n\n"
        f"Выберите характеристику для улучшения:",
        reply_markup=kb
    )

@router.callback_query(F.data.startswith("stat_"))
async def cb_upgrade_stat(cb: CallbackQuery):
    stat = cb.data.split("_")[1]
    cost = 100
    user = await get_user(cb.from_user.id)
    if user['galeons'] < cost:
        await cb.answer("Недостаточно галеонов!", show_alert=True)
        return
    await update_user(cb.from_user.id, galeons=user['galeons'] - cost, **{stat: user[stat] + 1})
    await cb.answer(f"✅ +1 к {stat}!")
    user = await get_user(cb.from_user.id)
    await cb.message.edit_text(format_profile(user, cb.from_user.first_name), reply_markup=profile_kb(user))
