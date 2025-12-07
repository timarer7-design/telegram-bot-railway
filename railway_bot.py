import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Получаем данные из переменных окружения Railway
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

# Проверяем наличие токена
if not BOT_TOKEN:
    print("❌ ОШИБКА: Не установлен BOT_TOKEN!")
    print("Добавьте переменную BOT_TOKEN в настройках Railway")
    exit(1)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

print("=" * 50)
print("🤖 TELEGRAM BOT ON RAILWAY")
print("=" * 50)
print(f"✅ Токен получен: {BOT_TOKEN[:15]}...")
print(f"👑 Админ ID: {ADMIN_ID or 'Не установлен'}")
print("=" * 50)

# Хранение информации о пользователях для ответов
user_data = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n"
        f"Я бот, работающий 24/7 на сервере Railway!\n"
        f"Напишите сообщение, и администратор получит его."
    )
    logger.info(f"Пользователь {user.id} вызвал /start")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "📋 **Доступные команды:**\n"
        "/start - Начать диалог\n"
        "/help - Помощь\n"
        "/status - Статус бота\n\n"
        "Просто напишите сообщение, и я передам его администратору!",
        parse_mode="Markdown"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status"""
    await update.message.reply_text(
        "✅ **Бот работает нормально!**\n"
        "🟢 Статус: Online 24/7\n"
        "🏠 Хостинг: Railway.app\n"
        "⏰ Сервис: Активен",
        parse_mode="Markdown"
    )

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений от пользователей"""
    try:
        user = update.effective_user
        message = update.message.text
        
        # Сохраняем данные пользователя
        user_data[str(user.id)] = {
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
        
        # Формируем сообщение для админа
        admin_msg = (
            f"📨 **НОВОЕ СООБЩЕНИЕ**\n"
            f"👤 От: {user.first_name or ''} {user.last_name or ''}\n"
            f"📛 @{user.username or 'нет_username'}\n"
            f"🆔 ID: `{user.id}`\n"
            f"⏰ {update.message.date.strftime('%H:%M:%S')}\n"
            f"━━━━━━━━━━━━━━\n"
            f"{message}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💬 Ответить: `/r {user.id} текст`"
        )
        
        # Отправляем админу, если ID установлен
        if ADMIN_ID:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_msg,
                parse_mode="Markdown"
            )
            logger.info(f"Сообщение от {user.id} отправлено админу")
        
        # Подтверждаем пользователю
        await update.message.reply_text(
            "✅ Сообщение отправлено администратору!\n"
            "Он ответит вам в ближайшее время."
        )
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("❌ Ошибка при отправке сообщения")

async def admin_reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /r для ответа админа"""
    try:
        # Проверяем, что это админ
        if str(update.effective_user.id) != ADMIN_ID:
            await update.message.reply_text("❌ Эта команда только для администратора")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "📝 Формат: `/r ID_пользователя ваш текст`\n\n"
                "Пример: `/r 123456789 Привет! Я получил твое сообщение.`",
                parse_mode="Markdown"
            )
            return
        
        user_id = context.args[0]
        reply_text = " ".join(context.args[1:])
        
        # Отправляем ответ пользователю
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📩 **Ответ от администратора:**\n\n{reply_text}\n\n"
                 f"_Вы можете продолжить диалог, просто напишите еще сообщение._",
            parse_mode="Markdown"
        )
        
        # Подтверждаем админу
        await update.message.reply_text(
            f"✅ Ответ отправлен пользователю {user_id}\n"
            f"Текст: {reply_text[:50]}..."
        )
        
        logger.info(f"Админ ответил пользователю {user_id}")
        
    except Exception as e:
        error_msg = str(e)
        if "chat not found" in error_msg.lower():
            await update.message.reply_text(
                f"❌ Не удалось отправить сообщение пользователю.\n"
                f"Возможно, пользователь не начинал диалог с ботом."
            )
        else:
            await update.message.reply_text(f"❌ Ошибка: {error_msg[:100]}")
        logger.error(f"Ошибка ответа админа: {e}")

def main():
    """Основная функция запуска бота"""
    print("🚀 Инициализация бота...")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("r", admin_reply_command))
    
    # Обработчик обычных сообщений (только от не-админов)
    if ADMIN_ID:
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~filters.User(user_id=int(ADMIN_ID)),
            handle_user_message
        ))
    else:
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_user_message
        ))
    
    print("✅ Бот инициализирован")
    print("📡 Запускаю polling...")
    print("=" * 50)
    
    # Запускаем бота
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
