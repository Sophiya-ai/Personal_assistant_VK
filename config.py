import os
from dotenv import load_dotenv

# Загрузка переменных окружения. Python по умолчанию не читает файл .env.
# Именно благодаря команде load_dotenv мы подгружаем переменные в наше окружение.
load_dotenv()

#Чтение переменных. Мы берем значения из .env файла и подставляем их в необходимые переменные.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_PROMPT_ID = os.getenv("OPENAI_PROMPT_ID")

#Настройки ВКонтакте. Здесь есть важное замечание: если в файле .env не прописана API-версия ВКонтакте, она возьмется как дефолтная (по умолчанию).
# Это нормальная практика для таких параметров, как версия API, порт или хост.
VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN")
VK_CONFIRMATION_TOKEN = os.getenv("VK_CONFIRMATION_TOKEN")
VK_SECRET = os.getenv("VK_SECRET")
VK_API_VERSION = os.getenv("VK_API_VERSION", "5.199")

# Настройки сервера. Мы задаем адрес и порт нашего сервера.
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

# Блок проверки ошибок. Этот блок проверяет, что мы не забыли указать нужные ключи и переменные окружения.
# Если какая-то переменная отсутствует, приложение сразу упадет, чтобы мы не гадали, почему ничего не работает.
def validate_config():
    required = {
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "OPENAI_PROMPT_ID": OPENAI_PROMPT_ID,
        "VK_GROUP_TOKEN": VK_GROUP_TOKEN,
        "VK_CONFIRMATION_TOKEN": VK_CONFIRMATION_TOKEN,
        "VK_SECRET": VK_SECRET,
    }

    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            f"Не заполнены переменные окружения: {', '.join(missing)}"
        )