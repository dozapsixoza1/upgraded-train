from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.users import get_or_create_user, get_user, update_user, add_grams
from database.clans import (
    create_clan, get_clan, get_clan_by_name, get_clan_members,
    delete_clan, remove_member, set_deputy, transfer_clan,
    add_application, get_applications, accept_application, get_top_clans
)
from config import CLAN_CREATE_COST, CLAN_BONUS_AMOUNT, CLAN_BONUS_COOLDOWN_HOURS

router = Router()

class ClanStates(StatesGroup):
    waiting_clan_name = State()
    waiting_search = State()

def clan_main_kb(user):
    buttons = []
    if user['clan_id']:
        buttons += [
            [InlineKeyboardButton(text="🏰 Мой клан", callback_data="clan_my")],
            [InlineKeyboardButton(text="🎁 Клановый бонус", callback_data="clan_bonus")],
            [InlineKeyboardButton(text="🚪 Покинуть клан", callback_data="clan_leave")],
        ]
    else:
        buttons += [
            [InlineKeyboardButton(text="➕ Создать клан", callback_data="clan_create")],
            [InlineKeyboardButton(text="🔍 Поиск клана", callback_data="clan_search")],
        ]
    buttons += [
        [InlineKeyboardButton(text="📋 Список кланов", callback_data="clan_list")],
        [InlineKeyboardButton(text="🏆 Топ кланов", callback_data="clan_top")],
    ]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.callback_query(F.data == "menu_clan")
async def cb_clan_menu(cb: CallbackQuery):
    user = await get_or_create_user(cb.from_user.id, cb.from_user.username, cb.from_user.first_name)
    await cb.message.edit_text("🏰 <b>Меню клана</b>", reply_markup=clan_main_kb(user))

@router.callback_query(F.data == "clan_create")
async def cb_clan_create(cb: CallbackQuery, state: FSMContext):
    user = await get_user(cb.from_user.id)
    if user['clan_id']:
        await cb.answer("Вы уже состоите в клане!", show_alert=True)
        return
    if user['grams'] < CLAN_CREATE_COST:
        await cb.answer(f"Нужно {CLAN_CREATE_COST:,} грамм для создания клана!", show_alert=True)
        return
    await state.set_state(ClanStates.waiting_clan_name)
    await cb.message.answer(
        f"✏️ Введите название клана (до 25 символов):\n"
        f"Стоимость создания: {CLAN_CREATE_COST:,} грамм"
    )

@router.message(ClanStates.waiting_clan_name)
async def process_clan_name(msg: Message, state: FSMContext):
    name = msg.text.strip()
    if len(name) > 25:
        await msg.reply("❌ Название слишком длинное (макс. 25 символов)!")
        return
    user = await get_user(msg.from_user.id)
    try:
        await update_user(msg.from_user.id, grams=user['grams'] - CLAN_CREATE_COST)
        await create_clan(name, msg.from_user.id)
        await state.clear()
        await msg.reply(f"🏰 Клан <b>{name}</b> успешно создан!\nПриглашайте участников по вашему ID: <code>{msg.from_user.id}</code>")
    except Exception as e:
        await update_user(msg.from_user.id, grams=user['grams'])  # refund
        await msg.reply("❌ Клан с таким названием уже существует!")

@router.callback_query(F.data == "clan_my")
async def cb_clan_my(cb: CallbackQuery):
    user = await get_user(cb.from_user.id)
    if not user['clan_id']:
        await cb.answer("Вы не в клане!", show_alert=True)
        return

    clan = await get_clan(user['clan_id'])
    members = await get_clan_members(user['clan_id'])
    total = sum(m['grams'] for m in members)

    is_owner = clan['owner_id'] == cb.from_user.id
    is_deputy = clan['deputy_id'] == cb.from_user.id

    text = (
        f"🏰 <b>Клан {clan['name']}</b>\n\n"
        f"👥 Участников: {len(members)}\n"
        f"💰 Общий баланс: {total:,} грамм\n\n"
    )

    buttons = []
    if is_owner or is_deputy:
        buttons.append([InlineKeyboardButton(text="📨 Заявки на вступление", callback_data="clan_applications")])
        buttons.append([InlineKeyboardButton(text="➕ Пригласить по ID", callback_data="clan_invite")])
    if is_owner:
        buttons.append([InlineKeyboardButton(text="❌ Удалить участника", callback_data="clan_kick")])
        buttons.append([InlineKeyboardButton(text="⭐️ Назначить зама", callback_data="clan_set_deputy")])
        buttons.append([InlineKeyboardButton(text="🔄 Передать клан", callback_data="clan_transfer")])
        buttons.append([InlineKeyboardButton(text="🗑 Удалить клан", callback_data="clan_delete")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="menu_clan")])

    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data == "clan_bonus")
async def cb_clan_bonus(cb: CallbackQuery):
    user = await get_user(cb.from_user.id)
    if not user['clan_id']:
        await cb.answer("Вы не в клане!", show_alert=True)
        return

    now = datetime.utcnow()
    if user['last_clan_bonus']:
        last = datetime.fromisoformat(user['last_clan_bonus'])
        diff = now - last
        if diff < timedelta(hours=CLAN_BONUS_COOLDOWN_HOURS):
            remaining = timedelta(hours=CLAN_BONUS_COOLDOWN_HOURS) - diff
            h = int(remaining.total_seconds() // 3600)
            m = int((remaining.total_seconds() % 3600) // 60)
            await cb.answer(f"⏳ Бонус будет через {h}ч {m}м", show_alert=True)
            return

    await add_grams(cb.from_user.id, CLAN_BONUS_AMOUNT)
    await update_user(cb.from_user.id, last_clan_bonus=now.isoformat())
    await cb.answer(f"🎁 Клановый бонус: +{CLAN_BONUS_AMOUNT:,} грамм!", show_alert=True)

@router.callback_query(F.data == "clan_leave")
async def cb_clan_leave(cb: CallbackQuery):
    user = await get_user(cb.from_user.id)
    clan = await get_clan(user['clan_id'])
    if clan and clan['owner_id'] == cb.from_user.id:
        await cb.answer("Владелец не может покинуть клан! Передайте или удалите клан.", show_alert=True)
        return
    await remove_member(cb.from_user.id)
    user = await get_user(cb.from_user.id)
    await cb.message.edit_text("✅ Вы покинули клан.", reply_markup=clan_main_kb(user))

@router.callback_query(F.data == "clan_delete")
async def cb_clan_delete(cb: CallbackQuery):
    user = await get_user(cb.from_user.id)
    clan = await get_clan(user['clan_id'])
    if not clan or clan['owner_id'] != cb.from_user.id:
        await cb.answer("Только владелец может удалить клан!", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data="clan_delete_confirm")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="clan_my")],
    ])
    await cb.message.edit_text("⚠️ Вы уверены? Это действие необратимо!", reply_markup=kb)

@router.callback_query(F.data == "clan_delete_confirm")
async def cb_clan_delete_confirm(cb: CallbackQuery):
    user = await get_user(cb.from_user.id)
    if user['clan_id']:
        await delete_clan(user['clan_id'])
    user = await get_user(cb.from_user.id)
    await cb.message.edit_text("🗑 Клан удалён.", reply_markup=clan_main_kb(user))

@router.callback_query(F.data == "clan_applications")
async def cb_clan_applications(cb: CallbackQuery):
    user = await get_user(cb.from_user.id)
    apps = await get_applications(user['clan_id'])
    if not apps:
        await cb.answer("Нет заявок на вступление.", show_alert=True)
        return
    buttons = []
    for app in apps:
        name = app.get('first_name') or app.get('username') or str(app['user_id'])
        buttons.append([
            InlineKeyboardButton(text=f"✅ {name}", callback_data=f"clan_accept_{app['user_id']}"),
            InlineKeyboardButton(text="❌", callback_data=f"clan_reject_{app['user_id']}"),
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="clan_my")])
    await cb.message.edit_text("📨 <b>Заявки на вступление:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.startswith("clan_accept_"))
async def cb_clan_accept(cb: CallbackQuery):
    applicant_id = int(cb.data.split("_")[2])
    user = await get_user(cb.from_user.id)
    await accept_application(user['clan_id'], applicant_id)
    await cb.answer("✅ Участник принят!")
    await cb_clan_applications(cb)

@router.callback_query(F.data.startswith("clan_reject_"))
async def cb_clan_reject(cb: CallbackQuery):
    applicant_id = int(cb.data.split("_")[2])
    user = await get_user(cb.from_user.id)
    from database.db import get_db
    async with await get_db() as db:
        await db.execute("DELETE FROM clan_applications WHERE clan_id=? AND user_id=?", (user['clan_id'], applicant_id))
        await db.commit()
    await cb.answer("❌ Заявка отклонена!")

@router.callback_query(F.data == "clan_top")
async def cb_clan_top(cb: CallbackQuery):
    clans = await get_top_clans(10)
    text = "🏆 <b>Топ кланов</b>\n\n"
    for i, c in enumerate(clans):
        total = c['total_grams'] or 0
        text += f"{i+1}. <b>{c['name']}</b> — {total:,} грамм ({c['member_count']} уч.)\n"
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_clan")]
    ]))

@router.callback_query(F.data == "clan_list")
async def cb_clan_list(cb: CallbackQuery):
    clans = await get_top_clans(20)
    text = "📋 <b>Список кланов</b>\n\n"
    for c in clans:
        text += f"• <b>{c['name']}</b> ({c['member_count']} уч.)\n"
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_clan")]
    ]))

@router.message(Command("клан"))
async def cmd_clan_top_n(msg: Message):
    parts = msg.text.strip().split()
    n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10
    n = min(n, 50)
    clans = await get_top_clans(n)
    text = f"🏆 <b>Топ {n} кланов</b>\n\n"
    for i, c in enumerate(clans):
        total = c['total_grams'] or 0
        text += f"{i+1}. <b>{c['name']}</b> — {total:,} грамм\n"
    await msg.answer(text)
