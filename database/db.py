import aiosqlite
from config import DB_PATH

def get_db():
    return aiosqlite.connect(DB_PATH)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            first_name  TEXT,
            grams       INTEGER DEFAULT 0,
            galeons     INTEGER DEFAULT 0,
            level       INTEGER DEFAULT 1,
            xp          INTEGER DEFAULT 0,
            rings       INTEGER DEFAULT 0,
            account_level INTEGER DEFAULT 1,
            clan_id     INTEGER,
            strength    INTEGER DEFAULT 10,
            agility     INTEGER DEFAULT 10,
            intellect   INTEGER DEFAULT 10,
            last_bonus  TEXT,
            last_clan_bonus TEXT,
            daily_attacks_date TEXT,
            daily_attacks_count INTEGER DEFAULT 0,
            skill_damage INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS duels (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            attacker_id INTEGER,
            defender_id INTEGER,
            winner_id   INTEGER,
            grams_won   INTEGER,
            galeons_won INTEGER,
            chat_id     INTEGER,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS transfers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id     INTEGER,
            to_id       INTEGER,
            amount      INTEGER,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS clans (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT UNIQUE,
            owner_id    INTEGER,
            deputy_id   INTEGER,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS clan_applications (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            clan_id     INTEGER,
            user_id     INTEGER,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS boss_sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id    INTEGER,
            boss_id     INTEGER,
            current_hp  INTEGER,
            started_at  TEXT DEFAULT (datetime('now')),
            finished    INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS boss_hits (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  INTEGER,
            user_id     INTEGER,
            damage      INTEGER,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS duel_cooldowns (
            user_id     INTEGER PRIMARY KEY,
            last_duel   TEXT
        );
        """)
        await db.commit()
