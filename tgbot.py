import logging
import os
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes

# --- CONFIG ---
BOT_TOKEN = os.environ["BOT_TOKEN"]

# --- CONVERSATION STATES ---
WAITING_FOR_THANK = 1

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

def save_thank(from_user, to_username, message, chat_id):
    conn = sqlite3.connect("dzenq.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO thanks (from_user_id, from_username, to_user_id, to_username, message, chat_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        from_user.id,
        from_user.username,
        None,
        to_username,
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
        "• Просто напиши @username дякую за допомогу\n"
        "• Або натисни /thank і я допоможу\n\n"
        "Команди:\n"
        "/thank — подякувати комусь\n"
        "/stats — твоя статистика подяк"
    )

async def thank_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Кому і за що хочеш подякувати?\n\nНаприклад: @natalia дякую за допомогу з багом")
    return WAITING_FOR_THANK

async def thank_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    from_user = message.from_user
    text = message.text or ""

    # Шукаємо @username в тексті
    mentioned_username = None
    for entity in (message.entities or []):
        if entity.type == "mention":
            mentioned_username = text[entity.offset + 1:entity.offset + entity.length]
            break

    if not mentioned_username:
        await message.reply_text("Не знайшов @username. Спробуй ще раз, наприклад: @natalia дякую за допомогу")
        return WAITING_FOR_THANK

    if mentioned_username == from_user.username:
        await message.reply_text("Собі не можна дякувати 😄 Спробуй ще раз.")
        return WAITING_FOR_THANK

    # Чистимо текст
    thank_text = text.replace(f"@{mentioned_username}", "").strip()

    save_thank(from_user, mentioned_username, thank_text, message.chat_id)

    await message.reply_text(
        f"💙 @{from_user.username} подякував @{mentioned_username}!\n"
        f"«{thank_text}»\n\n"
        f"Це збережено назавжди."
    )
    return ConversationHandler.END

async def thank_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Скасовано.")
    return ConversationHandler.END

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

    # Збираємо всі mentions
    mentions = []
    for entity in message.entities:
        if entity.type == "mention":
            username = text[entity.offset + 1:entity.offset + entity.length]
            mentions.append(username)

    if not mentions:
        return

    bot_username = (await context.bot.get_me()).username

    # В груповому чаті — потрібен тег бота
    if message.chat.type != "private":
        if bot_username not in mentions:
            return

    for mentioned_username in mentions:
        if mentioned_username == bot_username:
            continue
        if mentioned_username == from_user.username:
            continue

        # Чистимо текст
        thank_text = text
        for m in mentions:
            thank_text = thank_text.replace(f"@{m}", "")
        thank_text = thank_text.strip()

        save_thank(from_user, mentioned_username, thank_text, message.chat_id)

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

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("thank", thank_start)],
        states={
            WAITING_FOR_THANK: [MessageHandler(filters.TEXT & ~filters.COMMAND, thank_receive)],
        },
        fallbacks=[CommandHandler("cancel", thank_cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & filters.Entity("mention"), handle_mention))

    print("Бот запущено...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
