import sqlite3
import telebot
import os
from google import genai
from dotenv import load_dotenv

# Загружаем API-ключи из .env
load_dotenv()
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")  # Токен Telegram-бота
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Ключ для Google Gemini

# Инициализация бота и Google Gemini
bot = telebot.TeleBot(TG_BOT_TOKEN)
genai_client = genai.Client(api_key=GEMINI_API_KEY)

# Подключение к БД и создание таблиц
def init_db():
    conn = sqlite3.connect("fruits_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            age INTEGER,
            favorite_color TEXT,
            personality TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()  # Запускаем создание базы данных при старте


# Функция общения с Gemini API
def get_fruit_suggestion(name, age, favorite_color, personality):
    prompt = (
        f"Человек:\n"
        f"- Имя: {name}\n"
        f"- Возраст: {age}\n"
        f"- Любимый цвет: {favorite_color}\n"
        f"- Личность: {personality}\n\n"
        "Какой фрукт ему больше всего подходит? Ответь названием фрукта, а затем кратким описанием, почему он соответствует этому человеку."
    )

    response = genai_client.models.generate_content(
        model="gemini-2.0-flash", contents=prompt
    )
    
    return response.text.strip()



# Обработчик команды /start
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет! 👋\n\n"
        "Добро пожаловать в увлекательный бот-тест \"Какой ты фрукт?\" 🍎🍌🥝\n\n"
        "Я помогу тебе узнать, какой фрукт лучше всего отражает твою личность! 🧐\n"
        "Для этого мне нужно задать тебе несколько вопросов. Отвечай честно!\n\n"
        "Давай начнём! Напиши своё имя:"
    )
    bot.register_next_step_handler(message, get_name)


# Обработчик команды /help
@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "❓ *Помощь* ❓\n\n"
        "Этот бот поможет тебе узнать, какой ты фрукт! 🍏🍓🥭\n\n"
        "✅ Отправь команду /start, чтобы начать тест.\n"
        "✅ Отвечай на вопросы честно, чтобы получить точный результат.\n"
        "✅ Если хочешь пройти тест заново, просто снова отправь /start.\n\n"
        "Если у тебя есть вопросы или проблемы — пиши мне! 😊"
    )


# Сбор данных от пользователя
def get_name(message):
    user_id = message.chat.id
    name = message.text

    conn = sqlite3.connect("fruits_bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users (user_id, name) VALUES (?, ?)", (user_id, name))
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, "Отлично! Сколько тебе лет?")
    bot.register_next_step_handler(message, get_age)


def get_age(message):
    user_id = message.chat.id
    age = message.text

    if not age.isdigit():
        bot.send_message(message.chat.id, "Пожалуйста, введи возраст числом.")
        bot.register_next_step_handler(message, get_age)
        return

    conn = sqlite3.connect("fruits_bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET age = ? WHERE user_id = ?", (int(age), user_id))
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, "Какой твой любимый цвет?")
    bot.register_next_step_handler(message, get_favorite_color)


def get_favorite_color(message):
    user_id = message.chat.id
    favorite_color = message.text

    conn = sqlite3.connect("fruits_bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET favorite_color = ? WHERE user_id = ?", (favorite_color, user_id))
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, "Как бы ты описал свою личность?")
    bot.register_next_step_handler(message, get_personality)

def get_personality(message):
    user_id = message.chat.id
    personality = message.text

    conn = sqlite3.connect("fruits_bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET personality = ? WHERE user_id = ?", (personality, user_id))
    conn.commit()

    # Получаем данные о пользователе
    cursor.execute("SELECT name, age, favorite_color, personality FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data:
        name, age, favorite_color, personality = user_data
        fruit_description = get_fruit_suggestion(name, age, favorite_color, personality)
        bot.send_message(message.chat.id, f"🌟 {fruit_description}")
    else:
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуй снова.")


# Запуск бота
print("Бот запущен...")
bot.polling()
