from database.db import get_db

async def get_or_create_user(user_id: int, username: str = None, first_name: str = None):
    async with get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
            user = await cur.fetchone()
        if not user:
            await db.execute(
                "INSERT INTO users (user_id, username, first_name) VALUES (?,?,?)",
                (user_id, username, first_name)
            )
            await db.commit()
            async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
                user = await cur.fetchone()
        return user

async def get_user(user_id: int):
    async with get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
            return await cur.fetchone()

async def update_user(user_id: int, **fields):
    if not fields:
        return
    sets = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [user_id]
    async with get_db() as db:
        await db.execute(f"UPDATE users SET {sets} WHERE user_id=?", vals)
        await db.commit()

async def add_grams(user_id: int, amount: int):
    async with get_db() as db:
        await db.execute("UPDATE users SET grams = grams + ? WHERE user_id=?", (amount, user_id))
        await db.commit()

async def add_galeons(user_id: int, amount: int):
    async with get_db() as db:
        await db.execute("UPDATE users SET galeons = galeons + ? WHERE user_id=?", (amount, user_id))
        await db.commit()

async def get_top_users(limit: int = 10):
    async with get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute(
            "SELECT * FROM users ORDER BY grams DESC LIMIT ?", (limit,)
        ) as cur:
            return await cur.fetchall()

async def log_transfer(from_id: int, to_id: int, amount: int):
    async with get_db() as db:
        await db.execute(
            "INSERT INTO transfers (from_id, to_id, amount) VALUES (?,?,?)",
            (from_id, to_id, amount)
        )
        await db.commit()

async def get_transfer_history(user_id: int, limit: int = 10):
    async with get_db() as db:
        db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with db.execute(
            "SELECT * FROM transfers WHERE from_id=? OR to_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, user_id, limit)
        ) as cur:
            return await cur.fetchall()
