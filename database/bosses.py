from database.db import get_db
from config import BOSSES

async def get_active_boss_session(owner_id: int, boss_id: int):
    async with await get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute(
            "SELECT * FROM boss_sessions WHERE owner_id=? AND boss_id=? AND finished=0",
            (owner_id, boss_id)
        ) as cur:
            return await cur.fetchone()

async def create_boss_session(owner_id: int, boss_id: int):
    boss = next(b for b in BOSSES if b["id"] == boss_id)
    async with await get_db() as db:
        await db.execute(
            "INSERT INTO boss_sessions (owner_id, boss_id, current_hp) VALUES (?,?,?)",
            (owner_id, boss_id, boss["hp"])
        )
        await db.commit()
        async with db.execute(
            "SELECT * FROM boss_sessions WHERE owner_id=? AND boss_id=? AND finished=0",
            (owner_id, boss_id)
        ) as cur:
            db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute(
            "SELECT last_insert_rowid() as id"
        ) as cur:
            row = await cur.fetchone()
            return row[0]

async def apply_damage(session_id: int, user_id: int, damage: int):
    async with await get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute("SELECT * FROM boss_sessions WHERE id=?", (session_id,)) as cur:
            session = await cur.fetchone()
        if not session or session["finished"]:
            return None, False

        new_hp = max(0, session["current_hp"] - damage)
        finished = new_hp == 0
        await db.execute(
            "UPDATE boss_sessions SET current_hp=?, finished=? WHERE id=?",
            (new_hp, int(finished), session_id)
        )
        await db.execute(
            "INSERT INTO boss_hits (session_id, user_id, damage) VALUES (?,?,?)",
            (session_id, user_id, damage)
        )
        # track skill damage
        await db.execute(
            "UPDATE users SET skill_damage = skill_damage + ? WHERE user_id=?",
            (damage, user_id)
        )
        await db.commit()
        return new_hp, finished

async def get_boss_leaderboard(session_id: int):
    async with await get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute(
            "SELECT bh.user_id, u.first_name, SUM(bh.damage) as total "
            "FROM boss_hits bh JOIN users u ON u.user_id=bh.user_id "
            "WHERE bh.session_id=? GROUP BY bh.user_id ORDER BY total DESC",
            (session_id,)
        ) as cur:
            return await cur.fetchall()

async def get_duel_history(chat_id: int, limit: int = 10):
    async with await get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute(
            "SELECT d.*, a.first_name as attacker_name, df.first_name as defender_name "
            "FROM duels d "
            "JOIN users a ON a.user_id=d.attacker_id "
            "JOIN users df ON df.user_id=d.defender_id "
            "WHERE d.chat_id=? ORDER BY d.created_at DESC LIMIT ?",
            (chat_id, limit)
        ) as cur:
            return await cur.fetchall()

async def log_duel(attacker_id, defender_id, winner_id, grams_won, galeons_won, chat_id):
    async with await get_db() as db:
        await db.execute(
            "INSERT INTO duels (attacker_id, defender_id, winner_id, grams_won, galeons_won, chat_id) "
            "VALUES (?,?,?,?,?,?)",
            (attacker_id, defender_id, winner_id, grams_won, galeons_won, chat_id)
        )
        await db.commit()
