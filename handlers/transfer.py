import re
from datetime import date
from aiogram import Router, F
from aiogram.types import Message

from database.users import get_or_create_user, get_user, update_user, log_transfer
from config import TRANSFER_LIMITS

router = Router()

async def get_daily_sent(user_id: int) -> int:
    """Calculate how much was sent today from transfer log."""
    from database.db import get_db
    today = str(date.today())
    async with await get_db() as db:
        async with db.execute(
            "SELECT COALESCE(SUM(amount),0) as total FROM transfers "
            "WHERE from_id=? AND date(created_at)=?",
            (user_id, today)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0

@router.message(F.text.lower().regexp(r'^(сумма|передать сумма)\s+\d+$') & F.reply_to_message)
async def cmd_transfer(msg: Message):
    # Parse amount
    parts = msg.text.strip().split()
    amount = int(parts[-1])

    if amount <= 0:
        await msg.reply("❌ Сумма должна быть больше нуля!")
        return

    target = msg.reply_to_message.from_user
    if target.id == msg.from_user.id:
        await msg.reply("❌ Нельзя отправить граммы самому себе!")
        return
    if target.is_bot:
        await msg.reply("❌ Нельзя отправить граммы боту!")
        return

    sender = await get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
    receiver = await get_or_create_user(target.id, target.username, target.first_name)

    # Check balance
    if sender['grams'] < amount:
        await msg.reply(f"❌ Недостаточно грамм! У вас: {sender['grams']:,}")
        return

    # Check daily limit
    limit = TRANSFER_LIMITS[sender['account_level']]
    if limit is not None:
        sent_today = await get_daily_sent(msg.from_user.id)
        if sent_today + amount > limit:
            remaining = max(0, limit - sent_today)
            await msg.reply(
                f"❌ Превышен дневной лимит!\n"
                f"Ваш лимит: {limit:,} грамм/сутки\n"
                f"Осталось сегодня: {remaining:,} грамм\n"
                f"Повысьте уровень аккаунта для увеличения лимита."
            )
            return

    # Execute transfer
    await update_user(msg.from_user.id, grams=sender['grams'] - amount)
    await update_user(target.id, grams=receiver['grams'] + amount)
    await log_transfer(msg.from_user.id, target.id, amount)

    await msg.reply(
        f"✅ <b>Перевод выполнен!</b>\n"
        f"📤 {msg.from_user.first_name} → {target.first_name}\n"
        f"💰 Сумма: <b>{amount:,}</b> грамм"
    )
