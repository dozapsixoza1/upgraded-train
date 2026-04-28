# Legit Bot 🎮

Telegram-бот с игровой механикой: граммы, дуэли, боссы Хогвартса, кланы.

## Установка

```bash
# Клонировать или скопировать проект
cd legit_bot

# Установить зависимости
pip install -r requirements.txt

# Задать токен бота
export BOT_TOKEN="ВАШ_ТОКЕН_ОТ_BOTFATHER"

# Запустить
python main.py
```

## Структура проекта

```
legit_bot/
├── main.py              # Точка входа
├── config.py            # Конфигурация: боссы, лимиты, константы
├── requirements.txt
├── database/
│   ├── db.py            # Инициализация SQLite, get_db()
│   ├── users.py         # CRUD пользователей, переводы
│   ├── clans.py         # CRUD кланов
│   └── bosses.py        # Сессии боссов, дуэли
└── handlers/
    ├── common.py        # /start, меню, баланс, история, бонус
    ├── profile.py       # /профиль, прокачка уровня и характеристик
    ├── transfer.py      # Передача грамм (сумма / передать сумма)
    ├── duels.py         # Дуэли
    ├── bosses.py        # Боссы Хогвартса
    ├── clans.py         # Управление кланами
    ├── shop.py          # Магический магазин
    └── leaderboard.py   # /топ(n)
```

## Команды бота

| Команда | Описание |
|---|---|
| `/start` | Начало работы |
| `меню` | Главное меню |
| `баланс` / `б` / `грамм` | Проверить баланс |
| `сумма [N]` (в ответ на сообщение) | Передать N грамм |
| `дуэль` (в ответ на сообщение) | Вызвать на дуэль |
| `/история` | История переводов и дуэлей |
| `/профиль` | Профиль пользователя |
| `/топ [N]` | Топ N пользователей (макс. 50) |
| `/клан [N]` | Топ N кланов (макс. 50) |
| `/бонус` | Ежедневный бонус (при нулевом балансе) |

## Деплой на VPS

```bash
# Через systemd
sudo nano /etc/systemd/system/legit-bot.service

[Unit]
Description=Legit Telegram Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/legit_bot
Environment=BOT_TOKEN=ВАШ_ТОКЕН
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target

sudo systemctl enable legit-bot
sudo systemctl start legit-bot
```
