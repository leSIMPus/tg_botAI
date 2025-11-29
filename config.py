import os
from dotenv import load_dotenv

load_dotenv()  # загружаем переменные окружения из .env

# ----- Telegram -----
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Токен бота от BotFather

# ----- OpenAI -----
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Ключ OpenAI
