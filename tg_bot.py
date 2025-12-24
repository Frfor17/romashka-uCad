import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import httpx
from tg_bot_config import TELEGRAM_BOT_TOKEN, FASTAPI_URL


# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🤖 Бот для работы с CAD API\n\n"
        "Доступные команды:\n"
        "/status - статус MCP сервера\n"
        "/docs - получить документы\n"
        "/cube [размер] - создать куб (по умолчанию 10мм)\n"
        "/sphere [размер] - создать сферу\n"
        "/cylinder [размер] - создать цилиндр\n"
        "/create [тип] [размер] - создать фигуру\n\n"
        "Пример: /cube 15"
    )

async def get_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить статус MCP сервера"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_URL}/api/mcp/status")
            data = response.json()
            
            tools = "\n".join(data.get("tools", []))
            await update.message.reply_text(
                f"✅ Статус: {data.get('status', 'unknown')}\n"
                f"📝 Описание: {data.get('description', '')}\n\n"
                f"🛠 Доступные инструменты:\n{tools}"
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def get_documents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить документы"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_URL}/api/cad/documents")
            data = response.json()
            
            result = data.get("result", {})
            await update.message.reply_text(
                f"📄 Документы:\n{result}"
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def create_cube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создать куб"""
    size = context.args[0] if context.args else "10"
    
    try:
        size_float = float(size)
        if size_float <= 0:
            await update.message.reply_text("❌ Размер должен быть больше 0")
            return
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FASTAPI_URL}/api/cad/create-shape",
                params={"shape_type": "cube", "size": size_float}
            )
            data = response.json()
            
            await update.message.reply_text(
                f"✅ Куб создан!\n"
                f"Размер: {size_float}мм\n"
                f"Результат: {data.get('result', 'Успешно')}"
            )
    except ValueError:
        await update.message.reply_text("❌ Размер должен быть числом")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def create_sphere(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создать сферу"""
    size = context.args[0] if context.args else "10"
    
    try:
        size_float = float(size)
        if size_float <= 0:
            await update.message.reply_text("❌ Размер должен быть больше 0")
            return
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FASTAPI_URL}/api/cad/create-shape",
                params={"shape_type": "sphere", "size": size_float}
            )
            data = response.json()
            
            await update.message.reply_text(
                f"✅ Сфера создана!\n"
                f"Размер: {size_float}мм\n"
                f"Результат: {data.get('result', 'Успешно')}"
            )
    except ValueError:
        await update.message.reply_text("❌ Размер должен быть числом")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def create_cylinder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создать цилиндр"""
    size = context.args[0] if context.args else "10"
    
    try:
        size_float = float(size)
        if size_float <= 0:
            await update.message.reply_text("❌ Размер должен быть больше 0")
            return
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FASTAPI_URL}/api/cad/create-shape",
                params={"shape_type": "cylinder", "size": size_float}
            )
            data = response.json()
            
            await update.message.reply_text(
                f"✅ Цилиндр создан!\n"
                f"Размер: {size_float}мм\n"
                f"Результат: {data.get('result', 'Успешно')}"
            )
    except ValueError:
        await update.message.reply_text("❌ Размер должен быть числом")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def create_test_cube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создать тестовый куб (сам откроет документ)"""
    size = context.args[0] if context.args else "10"
    
    try:
        size_float = float(size)
        if size_float <= 0:
            await update.message.reply_text("❌ Размер должен быть больше 0")
            return
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FASTAPI_URL}/api/cad/create-test-shape",
                params={"shape_type": "cube", "size": size_float}
            )
            data = response.json()
            
            await update.message.reply_text(
                f"✅ Тестовый куб создан!\n"
                f"Размер: {size_float}мм\n"
                f"Файл: {data.get('details', {}).get('file', 'Неизвестно')}\n"
                f"Результат: {data.get('message', 'Успешно')}"
            )
    except ValueError:
        await update.message.reply_text("❌ Размер должен быть числом")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def create_shape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создать любую фигуру"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Используй: /create [тип] [размер]\n"
            "Типы: cube, sphere, cylinder\n"
            "Пример: /create cube 15"
        )
        return
    
    shape_type = context.args[0].lower()
    size = context.args[1]
    
    valid_shapes = ["cube", "sphere", "cylinder"]
    if shape_type not in valid_shapes:
        await update.message.reply_text(
            f"❌ Неправильный тип. Доступно: {', '.join(valid_shapes)}"
        )
        return
    
    try:
        size_float = float(size)
        if size_float <= 0:
            await update.message.reply_text("❌ Размер должен быть больше 0")
            return
            
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FASTAPI_URL}/api/cad/create-shape",
                params={"shape_type": shape_type, "size": size_float}
            )
            data = response.json()
            
            shape_names = {
                "cube": "куб",
                "sphere": "сфера", 
                "cylinder": "цилиндр"
            }
            
            await update.message.reply_text(
                f"✅ {shape_names.get(shape_type, 'Фигура')} создана!\n"
                f"Тип: {shape_type}\n"
                f"Размер: {size_float}мм\n"
                f"Результат: {data.get('result', 'Успешно')}"
            )
    except ValueError:
        await update.message.reply_text("❌ Размер должен быть числом")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь"""
    await update.message.reply_text(
        "📋 Доступные команды:\n"
        "/start - начать работу\n"
        # "/status - статус сервера\n"
        # "/docs - получить документы\n"
        "/test_cube [размер] - создать тестовый кубы куб\n"
        # "/sphere [размер] - создать сферу\n"
        # "/cylinder [размер] - создать цилиндр\n"
        # "/create [тип] [размер] - создать фигуру\n\n"
        # "Примеры:\n"
        # "/cube 15\n"
        # "/sphere 20\n"
        # "/create cylinder 10"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    text = update.message.text.lower()
    
    if "привет" in text or "hello" in text:
        await update.message.reply_text("Привет! Напиши /help чтобы увидеть команды")
    elif "статус" in text:
        await get_status(update, context)
    elif "документ" in text:
        await get_documents(update, context)
    else:
        await update.message.reply_text(
            "Не понял команду. Напиши /help для списка команд"
        )

def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    # application.add_handler(CommandHandler("help", help_command))
    # application.add_handler(CommandHandler("status", get_status))
    # application.add_handler(CommandHandler("docs", get_documents))
    # application.add_handler(CommandHandler("cube", create_cube))
    # application.add_handler(CommandHandler("sphere", create_sphere))
    # application.add_handler(CommandHandler("cylinder", create_cylinder))
    # application.add_handler(CommandHandler("create", create_shape))
    application.add_handler(CommandHandler("test_cube", create_test_cube))
    # Обработка текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    print("🤖 Бот запущен! Остановите бота через Ctrl+C")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()