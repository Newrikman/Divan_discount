import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Подключение к базе данных
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

# Создание таблицы пользователей
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE,
    name TEXT,
    surname TEXT,
    birth_date TEXT,
    phone TEXT,
    total_spent REAL DEFAULT 0,
    discount INTEGER DEFAULT 0
)
""")
conn.commit()

# Функция для регистрации пользователя
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать! Для регистрации отправьте свои данные в формате:\n"
        "Имя Фамилия Дата_рождения Номер_телефона\n"
        "Пример: Иван Иванов 1990-01-01 +998901234567"
    )

async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = update.message.text.split()
        name, surname, birth_date, phone = data
        telegram_id = update.message.from_user.id

        cursor.execute("""
        INSERT OR IGNORE INTO users (telegram_id, name, surname, birth_date, phone)
        VALUES (?, ?, ?, ?, ?)
        """, (telegram_id, name, surname, birth_date, phone))
        conn.commit()

        await update.message.reply_text("Вы успешно зарегистрированы!")
    except Exception as e:
        await update.message.reply_text("Ошибка регистрации. Проверьте формат данных.")

async def add_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        telegram_id = update.message.from_user.id
        amount = float(update.message.text.split()[1])

        cursor.execute("SELECT total_spent FROM users WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()

        if result:
            total_spent = result[0] + amount

            # Рассчитываем скидку
            if total_spent >= 20000000:
                discount = 20
            elif total_spent >= 15000000:
                discount = 15
            elif total_spent >= 10000000:
                discount = 10
            elif total_spent >= 5000000:
                discount = 5
            else:
                discount = 0

            # Обновляем данные
            cursor.execute("""
            UPDATE users
            SET total_spent = ?, discount = ?
            WHERE telegram_id = ?
            """, (total_spent, discount, telegram_id))
            conn.commit()

            await update.message.reply_text(
                f"Чек добавлен! Всего потрачено: {total_spent} сум. Ваша скидка: {discount}%."
            )
        else:
            await update.message.reply_text("Вы не зарегистрированы. Введите /start для регистрации.")
    except Exception as e:
        await update.message.reply_text("Ошибка при добавлении чека. Введите сумму в формате: /add сумма.")

async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    cursor.execute("SELECT name, total_spent, discount FROM users WHERE telegram_id = ?", (telegram_id,))
    result = cursor.fetchone()

    if result:
        name, total_spent, discount = result
        await update.message.reply_text(
            f"Имя: {name}\nВсего потрачено: {total_spent} сум\nВаша скидка: {discount}%."
        )
    else:
        await update.message.reply_text("Вы не зарегистрированы. Введите /start для регистрации.")

# Основная функция
def main():
    app = ApplicationBuilder().token("8017053987:AAE9vEiYCFmAZd4KeQ1eRuCjNgCbnKHWKhk").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, register_user))
    app.add_handler(CommandHandler("add", add_receipt))
    app.add_handler(CommandHandler("status", check_status))

    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
