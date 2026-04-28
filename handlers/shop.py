from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from database.users import get_user, update_user
from database.db import get_db
from config import BOSSES

router = Router()

SHOP_ITEMS = [
    {"id": "attack_x1",  "name": "🗡 1 удар по боссу",   "cost": 500,   "attacks": 1},
    {"id": "attack_x5",  "name": "🗡 5 ударов по боссу",  "cost": 2000,  "attacks": 5},
    {"id": "attack_x10", "name": "🗡 10 ударов по боссу", "cost": 3500,  "attacks": 10},
]

def shop_kb():
    buttons = []
    for item in SHOP_ITEMS:
        buttons.append([InlineKeyboardButton(
            text=f"{item['name']} — {item['cost']:,} грамм",
            callback_data=f"shop_buy_{item['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.callback_query(F.data == "menu_shop")
async def cb_shop(cb: CallbackQuery):
    user = await get_user(cb.from_user.id)
    await cb.message.edit_text(
        f"🛒 <b>Магический магазин</b>\n\n"
        f"💰 Ваш баланс: {user['grams']:,} грамм\n\n"
        f"Купленные удары применяются автоматически при следующей атаке на босса.",
        reply_markup=shop_kb()
    )

@router.callback_query(F.data.startswith("shop_buy_"))
async def cb_shop_buy(cb: CallbackQuery):
    item_id = cb.data[len("shop_buy_"):]
    item = next((i for i in SHOP_ITEMS if i["id"] == item_id), None)
    if not item:
        await cb.answer("Товар не найден!", show_alert=True)
        return

    user = await get_user(cb.from_user.id)
    if user['grams'] < item['cost']:
        await cb.answer(f"Недостаточно грамм! Нужно {item['cost']:,}", show_alert=True)
        return

    # Reduce daily attack count = give free attacks back
    new_count = max(0, user['daily_attacks_count'] - item['attacks'])
    await update_user(cb.from_user.id,
                      grams=user['grams'] - item['cost'],
                      daily_attacks_count=new_count)

    await cb.answer(f"✅ Куплено: {item['name']}!", show_alert=True)
    user = await get_user(cb.from_user.id)
    await cb.message.edit_text(
        f"🛒 <b>Магический магазин</b>\n\n"
        f"💰 Ваш баланс: {user['grams']:,} грамм\n\n"
        f"Купленные удары применяются автоматически при следующей атаке на босса.",
        reply_markup=shop_kb()
    )
