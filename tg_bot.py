import asyncio # не знаю, вроде не испольузуется, поправьте меня
import logging  # библа для логов, чтобы легче дебагать было
from telegram import Update # сама библа для тг бота
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes # сама библа для тг бота
import httpx
from tg_bot_config import TELEGRAM_BOT_TOKEN, FASTAPI_URL # токены и прочее для связи
import sqlite3 # первичная бд, где храним всякое, пока чисто юзеров
from datetime import datetime # тип данных, где-то "рядом с" или "в" бд используется

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_NAME = 'bot_users.db'  # Имя файла базы

# Создание БД при первом запуске
def init_db():  # создаём функцию для ну, для бд, инициализации бд
    conn = sqlite3.connect(DB_NAME) # делаем подключение через функцию connect
    cur = conn.cursor() 
    # если есть файл с DB_NAME именем, то к нему подрубаемся, если нет, то новый делаем

    # Проверяем, есть ли уже таблица
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    table_exists = cur.fetchone() # курсор - это объект для выполнения sql команд
    # как сказал дипсик, и к сожалению лучше я не скажу:
    # если conn - это тоннель к бд, то cur это грузовик, который возит SQL запросы туда, и
    # и результаты обратно

    if table_exists:  # если таблицы нет, то как бы да, чисто проверка
        print(f"Таблица 'users' уже существует в {DB_NAME}")
    else:
        print(f"Создаю таблицу 'users' в {DB_NAME}")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                first_seen DATETIME,
                last_seen DATETIME
            )
        ''')
        conn.commit() # коммит - это физическая запись изменений на диск, на жёсткий полагаю, хз, типо наверн до этого оно хранится в оперативке
        print("Таблица создана успешно") # тут выполняет SQL-запрос, для создания бд как видите
    conn.close() # закрывает файловый дескриптор файла DB_NAME, освобождает память занятую объктом Connection

# чисто следить сколько вообще пользователей есть
# Функция для записи/обновления пользователя
def log_user(user):  # ну создаём функцию, в аргументе надо отправить Id Или чёто такое как видите
    # курсор и коннект, как в прошлом буквально
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Проверяем, есть ли пользователь уже в базе
    cur.execute('SELECT user_id FROM users WHERE user_id = ?', (user.id,)) # проверяем, мб он уже есть
    exists = cur.fetchone() # получает первую строку или none

    # логика обновления и вставки
    
    if exists:
        # Обновляем время последнего визита
        cur.execute('''
            UPDATE users 
            SET last_seen = ?, username = ?, first_name = ?, last_name = ?
            WHERE user_id = ?
        ''', (datetime.now(), user.username, user.first_name, user.last_name, user.id)) # дейтам время автоматом в строку сохраняет
    else:
        # Добавляем нового пользователя
        cur.execute('''
            INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user.id, user.username, user.first_name, user.last_name, datetime.now(), datetime.now()))
    
    # ну комит клоуз в прошлом разбирали
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🤖 Бот для работы с CAD API\n\n"
        "Доступные команды:\n"
        "/status - статус MCP сервера\n"
        # "/docs - получить документы\n"
        "/create_cube [размер] - создать Куб (по умолчанию 10мм)\n"
        # "/sphere [размер] - создать сферу\n"
        # "/cylinder [размер] - создать цилиндр\n"
        # "/create [тип] [размер] - создать фигуру\n\n"
        # "Пример: /cube 15"
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

    log_user(message.from_user)
    
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

            # 2. Получаем имя файла из ответа
            filename = data.get('details', {}).get('file', 'cube.stl')
            #тут получаем имя файла крч




            download_url = f"{FASTAPI_URL}/api/cad/download/{filename}"
            
            # 3. Скачиваем файл в память
            file_response = await client.get(download_url)
            # вот тут сам файл хранится по идее
            
            # 4. Отправляем файл пользователю
            await update.message.reply_document(
                document=file_response.content,
                filename=filename,
                caption=f"✅ Куб создан!\nРазмер: {size_float}мм"
            )
            
            await update.message.reply_text(
                f"✅ Куб создан!\n"
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):  #эта функция, когда боту пишут любое текст сообщение
    # как видите, функция получается Update, то есть объект, который тг отправляет в функцию
    # в объекте Update лежит вся инфа, контент сообщения имя пользователя и вообще всё что надо
    # второй арг - Context это реально контекст, это типо не апдайт, а именно контекст
    # внутри контекст хранится такое малое хранилище данных, локальное, чё вообще происходит, не точечно, а в общем и целом
    """Обработка текстовых сообщений"""
    text = update.message.text.lower()  # тут присаивание переменной, из аргумента Update
    # который передали в функцию, мы достаём подобъект message.text и не просто достаёт, а сразу делаем lower()
    # и короче это ну, делает сообщение из малых символов, и сохраняем в переменную text

    log_user(update.message.from_user) # тут вызывается функция связанна с бд
    # в аргументе как видите, мы берём из Update имя юзера и сохраняем
    # чисто сделано чтобы считать, сколько и кто юзает бота, без доп инфы, чисто имя



    # снизу просто простейшая логика команд начальная, надо переделать
    # типо оно говорит особую фразу, если у тебя есть привет и другие особые фразы, также вызывает команды вроде, если у тебя особые слова
    # ну бред короче, надо переделать
    
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
    application.add_handler(CommandHandler("create_cube", create_test_cube))
    # Обработка текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    print("🤖 Бот запущен! Остановите бота через Ctrl+C")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    init_db()
    main()