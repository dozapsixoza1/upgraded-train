from database.db import get_db

async def create_clan(name: str, owner_id: int):
    async with await get_db() as db:
        await db.execute("INSERT INTO clans (name, owner_id) VALUES (?,?)", (name, owner_id))
        await db.execute("UPDATE users SET clan_id=(SELECT id FROM clans WHERE name=?) WHERE user_id=?", (name, owner_id))
        await db.commit()

async def get_clan(clan_id: int):
    async with await get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute("SELECT * FROM clans WHERE id=?", (clan_id,)) as cur:
            return await cur.fetchone()

async def get_clan_by_name(name: str):
    async with await get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute("SELECT * FROM clans WHERE name LIKE ?", (f"%{name}%",)) as cur:
            return await cur.fetchall()

async def get_clan_members(clan_id: int):
    async with await get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute("SELECT * FROM users WHERE clan_id=?", (clan_id,)) as cur:
            return await cur.fetchall()

async def delete_clan(clan_id: int):
    async with await get_db() as db:
        await db.execute("UPDATE users SET clan_id=NULL WHERE clan_id=?", (clan_id,))
        await db.execute("DELETE FROM clans WHERE id=?", (clan_id,))
        await db.execute("DELETE FROM clan_applications WHERE clan_id=?", (clan_id,))
        await db.commit()

async def remove_member(user_id: int):
    async with await get_db() as db:
        await db.execute("UPDATE users SET clan_id=NULL WHERE user_id=?", (user_id,))
        await db.commit()

async def set_deputy(clan_id: int, deputy_id: int):
    async with await get_db() as db:
        await db.execute("UPDATE clans SET deputy_id=? WHERE id=?", (deputy_id, clan_id))
        await db.commit()

async def transfer_clan(clan_id: int, new_owner_id: int):
    async with await get_db() as db:
        await db.execute("UPDATE clans SET owner_id=?, deputy_id=NULL WHERE id=?", (new_owner_id, clan_id))
        await db.commit()

async def add_application(clan_id: int, user_id: int):
    async with await get_db() as db:
        await db.execute("INSERT OR IGNORE INTO clan_applications (clan_id, user_id) VALUES (?,?)", (clan_id, user_id))
        await db.commit()

async def get_applications(clan_id: int):
    async with await get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute(
            "SELECT ca.*, u.first_name, u.username FROM clan_applications ca "
            "JOIN users u ON u.user_id=ca.user_id WHERE ca.clan_id=?", (clan_id,)
        ) as cur:
            return await cur.fetchall()

async def accept_application(clan_id: int, user_id: int):
    async with await get_db() as db:
        await db.execute("UPDATE users SET clan_id=? WHERE user_id=?", (clan_id, user_id))
        await db.execute("DELETE FROM clan_applications WHERE clan_id=? AND user_id=?", (clan_id, user_id))
        await db.commit()

async def get_top_clans(limit: int = 10):
    async with await get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute(
            "SELECT c.id, c.name, SUM(u.grams) as total_grams, COUNT(u.user_id) as member_count "
            "FROM clans c LEFT JOIN users u ON u.clan_id=c.id "
            "GROUP BY c.id ORDER BY total_grams DESC LIMIT ?", (limit,)
        ) as cur:
            return await cur.fetchall()
