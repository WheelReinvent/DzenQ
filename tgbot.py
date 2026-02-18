import logging
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIG ---
BOT_TOKEN = os.environ.get("BOT_TOKEN") # від @BotFather

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect("dzenq.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS thanks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER,
            from_username TEXT,
            to_user_id INTEGER,
            to_username TEXT,
            message TEXT,
            chat_id INTEGER,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_thank(from_user, to_user, message, chat_id):
    conn = sqlite3.connect("dzenq.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO thanks (from_user_id, from_username, to_user_id, to_username, message, chat_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        from_user.id,
        from_user.username,
        to_user.id,
        to_user.username,
        message,
        chat_id,
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

def get_stats(username):
    conn = sqlite3.connect("dzenq.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM thanks WHERE to_username = ?", (username,))
    received = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM thanks WHERE from_username = ?", (username,))
    sent = c.fetchone()[0]
    conn.close()
    return received, sent

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привіт! Я @dzenq_bot — бот подяк.\n\n"
        "Як подякувати:\n"
        "@dzenq_bot @username дякую за допомогу з багом!\n\n"
        "Команди:\n"
        "/stats — твоя статистика подяк"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    if not username:
        await update.message.reply_text("Встанови username в Telegram щоб бачити статистику.")
        return
    received, sent = get_stats(username)
    await update.message.reply_text(
        f"📊 Статистика @{username}:\n"
        f"✅ Отримано подяк: {received}\n"
        f"💙 Відправлено подяк: {sent}"
    )

async def handle_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.entities:
        return

    from_user = message.from_user
    text = message.text or ""

    # Шукаємо згадки інших юзерів (не бота)
    for entity in message.entities:
        if entity.type == "mention":
            mentioned_username = text[entity.offset + 1:entity.offset + entity.length]  # без @

            # Ігноруємо якщо дякує сам собі
            if mentioned_username == from_user.username:
                continue

            # Ігноруємо самого бота
            if mentioned_username == context.bot.username:
                continue

            # Отримуємо текст подяки (все крім @mention)
            thank_text = text.replace(f"@{mentioned_username}", "").replace(f"@{context.bot.username}", "").strip()

            # Зберігаємо подяку
            # to_user - спрощено, тільки username (без id бо mention не дає id)
            class SimpleUser:
                def __init__(self, username):
                    self.id = None
                    self.username = username

            save_thank(from_user, SimpleUser(mentioned_username), thank_text, message.chat_id)

            await message.reply_text(
                f"💙 @{from_user.username} подякував @{mentioned_username}!\n"
                f"«{thank_text}»\n\n"
                f"Це збережено назавжди. /stats щоб побачити репутацію."
            )

# --- MAIN ---
def main():
    init_db()
    logging.basicConfig(level=logging.INFO)

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & filters.Entity("mention"), handle_mention))

    print("Бот запущено...")
    app.run_polling()

if __name__ == "__main__":
    main()
