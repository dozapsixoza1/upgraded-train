import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
DB_PATH = "legit.db"

# Bosses config
BOSSES = [
    {"id": 1, "name": "Гарри Поттер",         "hp": 1_000,       "reward": 50,     "min_level": 1,   "rings_required": 0},
    {"id": 2, "name": "Рон Уизли",             "hp": 5_000,       "reward": 80,     "min_level": 1,   "rings_required": 1},
    {"id": 3, "name": "Гермиона Грейнджер",    "hp": 25_000,      "reward": 150,    "min_level": 7,   "rings_required": 2},
    {"id": 4, "name": "Рубеус Хагрид",         "hp": 100_000,     "reward": 400,    "min_level": 12,  "rings_required": 3},
    {"id": 5, "name": "Ремус Люпин",           "hp": 250_000,     "reward": 1000,   "min_level": 20,  "rings_required": 4},
    {"id": 6, "name": "Сивилла Трелони",       "hp": 750_000,     "reward": 2500,   "min_level": 27,  "rings_required": 5},
    {"id": 7, "name": "Аргус Филч",            "hp": 2_000_000,   "reward": 5000,   "min_level": 35,  "rings_required": 6},
    {"id": 8, "name": "Сириус Блэк",           "hp": 5_000_000,   "reward": 10000,  "min_level": 50,  "rings_required": 7},
    {"id": 9, "name": "Минерва МакГонагалл",   "hp": 15_000_000,  "reward": 20000,  "min_level": 70,  "rings_required": 8},
    {"id": 10,"name": "Северус Снейп",         "hp": 50_000_000,  "reward": 50000,  "min_level": 100, "rings_required": 9},
    {"id": 11,"name": "Альбус Дамблдор",       "hp": 250_000_000, "reward": 150000, "min_level": 150, "rings_required": 10},
]

# Transfer limits per account level
TRANSFER_LIMITS = {
    1: 5_000,
    2: 10_000,
    3: 25_000,
    4: 50_000,
    5: None,  # unlimited
}

LEVEL_UPGRADE_COSTS = {
    2: 5_000,
    3: 10_000,
    4: 25_000,
    5: 50_000,
}

CLAN_CREATE_COST = 50_000
CLAN_BONUS_AMOUNT = 1_000
CLAN_BONUS_COOLDOWN_HOURS = 48

DUEL_COOLDOWN_MINUTES = 10
BOSS_DAILY_FREE_ATTACKS = 8
BOSS_EXTRA_ATTACK_COST = 500  # grams per extra attack
