from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from database.users import get_user, update_user, get_or_create_user
from database.db import get_db
from config import ADMIN_IDS

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ── Выдать граммы ──────────────────────────────────────────────
# /addgrams [user_id] [amount]
@router.message(Command("addgrams"))
async def cmd_add_grams(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.strip().split()
    if len(parts) != 3 or not parts[1].lstrip("-").isdigit() or not parts[2].lstrip("-").isdigit():
        await msg.reply("Использование: /addgrams [user_id] [amount]")
        return
    target_id, amount = int(parts[1]), int(parts[2])
    user = await get_user(target_id)
    if not user:
        await msg.reply("❌ Пользователь не найден.")
        return
    new_grams = max(0, user['grams'] + amount)
    await update_user(target_id, grams=new_grams)
    action = f"+{amount}" if amount >= 0 else str(amount)
    await msg.reply(
        f"✅ Граммы обновлены\n"
        f"👤 ID: {target_id}\n"
        f"💰 Изменение: {action}\n"
        f"💰 Новый баланс: {new_grams:,}"
    )

# ── Забрать граммы ─────────────────────────────────────────────
# /takegrams [user_id] [amount]
@router.message(Command("takegrams"))
async def cmd_take_grams(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.strip().split()
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        await msg.reply("Использование: /takegrams [user_id] [amount]")
        return
    target_id, amount = int(parts[1]), int(parts[2])
    user = await get_user(target_id)
    if not user:
        await msg.reply("❌ Пользователь не найден.")
        return
    new_grams = max(0, user['grams'] - amount)
    await update_user(target_id, grams=new_grams)
    await msg.reply(
        f"✅ Граммы списаны\n"
        f"👤 ID: {target_id}\n"
        f"💰 Списано: {amount:,}\n"
        f"💰 Остаток: {new_grams:,}"
    )

# ── Забанить ───────────────────────────────────────────────────
# /ban [user_id]
@router.message(Command("ban"))
async def cmd_ban(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.reply("Использование: /ban [user_id]")
        return
    target_id = int(parts[1])
    user = await get_user(target_id)
    if not user:
        await msg.reply("❌ Пользователь не найден.")
        return
    await update_user(target_id, is_banned=1)
    await msg.reply(f"🚫 Пользователь {target_id} забанен.")

# ── Разбанить ──────────────────────────────────────────────────
# /unban [user_id]
@router.message(Command("unban"))
async def cmd_unban(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.reply("Использование: /unban [user_id]")
        return
    target_id = int(parts[1])
    await update_user(target_id, is_banned=0)
    await msg.reply(f"✅ Пользователь {target_id} разбанен.")

# ── Сброс баланса и статистики ─────────────────────────────────
# /resetuser [user_id]
@router.message(Command("resetuser"))
async def cmd_reset_user(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.reply("Использование: /resetuser [user_id]")
        return
    target_id = int(parts[1])
    user = await get_user(target_id)
    if not user:
        await msg.reply("❌ Пользователь не найден.")
        return
    await update_user(target_id,
        grams=0, galeons=0, xp=0, rings=0,
        strength=10, agility=10, intellect=10,
        account_level=1, skill_damage=0,
        daily_attacks_count=0, daily_attacks_date=None,
        last_bonus=None, last_clan_bonus=None
    )
    await msg.reply(f"🔄 Статистика пользователя {target_id} сброшена.")

# ── Рассылка ───────────────────────────────────────────────────
# /broadcast [текст]
@router.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    text = msg.text[len("/broadcast"):].strip()
    if not text:
        await msg.reply("Использование: /broadcast [текст сообщения]")
        return

    async with get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute("SELECT user_id FROM users") as cur:
            users = await cur.fetchall()

    sent, failed = 0, 0
    for u in users:
        try:
            await msg.bot.send_message(u['user_id'], f"📢 <b>Объявление</b>\n\n{text}")
            sent += 1
        except Exception:
            failed += 1

    await msg.reply(f"📢 Рассылка завершена\n✅ Отправлено: {sent}\n❌ Не доставлено: {failed}")

# ── Статистика бота ────────────────────────────────────────────
# /adminstats
@router.message(Command("adminstats"))
async def cmd_admin_stats(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    async with get_db() as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total_users = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_banned=1") as cur:
            banned = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM duels") as cur:
            total_duels = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM clans") as cur:
            total_clans = (await cur.fetchone())[0]
        async with db.execute("SELECT COALESCE(SUM(grams),0) FROM users") as cur:
            total_grams = (await cur.fetchone())[0]

    await msg.reply(
        f"📊 <b>Статистика Legit</b>\n\n"
        f"👥 Пользователей: {total_users:,}\n"
        f"🚫 Забанено: {banned}\n"
        f"⚔️ Дуэлей сыграно: {total_duels:,}\n"
        f"🏰 Кланов: {total_clans}\n"
        f"💰 Всего грамм в игре: {total_grams:,}"
)
