import uuid
import requests

from config import OPENROUTER_API_KEY
from db import (
    get_conversation_id,
    save_conversation_id,
    get_conversation_history,
    save_message,
    clear_conversation_history,
)

# Импортируем системный промпт и поиск по базе знаний
from prompt import SYSTEM_PROMPT
from knowledge_base import search_knowledge, load_knowledge_base

# URL API OpenRouter (совместим с форматом OpenAI)
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Модель, которую используем (бесплатная)
MODEL_NAME = "openai/gpt-oss-120b:free"

# Загружаем базу знаний при старте
load_knowledge_base()


def get_or_create_conversation(vk_user_id: int) -> str:
    """
    Получает существующий ID разговора или создаёт новый.
    Нужен для отслеживания, какая история принадлежит какому пользователю.
    """
    existing_id = get_conversation_id(vk_user_id)
    if existing_id:
        return existing_id

    # Генерируем уникальный ID разговора
    conversation_id = str(uuid.uuid4())
    save_conversation_id(vk_user_id, conversation_id)
    return conversation_id


def ask_openai(vk_user_id: int, user_text: str) -> str:
    """
    Главная функция: принимает текст от пользователя,
    ищет релевантную информацию в базе знаний,
    отправляет всё в OpenRouter и возвращает ответ.
    """
    conversation_id = get_or_create_conversation(vk_user_id)

    # ====== ПОИСК ПО БАЗЕ ЗНАНИЙ ======
    # Ищем фрагменты, похожие на вопрос пользователя
    # Это аналог File Search в OpenAI
    knowledge_context = search_knowledge(user_text, n_results=3)

    # ====== ФОРМИРУЕМ СИСТЕМНОЕ СООБЩЕНИЕ ======
    # Если нашли что-то в базе знаний — добавляем к системному промпту
    if knowledge_context:
        system_message = (
            f"{SYSTEM_PROMPT}\n\n"
            f"=== БАЗА ЗНАНИЙ ===\n"
            f"Ниже приведена информация из базы знаний. "
            f"Используй её для ответа на вопрос пользователя:\n\n"
            f"{knowledge_context}\n"
            f"=== КОНЕЦ БАЗЫ ЗНАНИЙ ==="
        )
    else:
        system_message = SYSTEM_PROMPT

    # ====== ПОЛУЧАЕМ ИСТОРИЮ СООБЩЕНИЙ ======
    # Загружаем последние 10 сообщений для контекста разговора
    history = get_conversation_history(vk_user_id, limit=10)

    # ====== СОБИРАЕМ МАССИВ СООБЩЕНИЙ ======
    # Формат OpenRouter совместим с OpenAI:
    # [системное сообщение, история, новое сообщение]
    messages = [
        {"role": "system", "content": system_message}  # Системный промпт + база знаний
    ] + history + [                                      # История диалога
        {"role": "user", "content": user_text}           # Текущий вопрос
    ]

    # ====== ЗАГОЛОВКИ ЗАПРОСА ======
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",  # API ключ OpenRouter
        "Content-Type": "application/json",
        "HTTP-Referer": "https://vk.com",                  # Откуда идёт запрос
        "X-Title": "VK Bot"                                # Название приложения
    }

    # ====== ТЕЛО ЗАПРОСА ======
    payload = {
        "model": MODEL_NAME,      # Какую модель использовать
        "messages": messages,      # Массив сообщений
        "temperature": 0.7,        # Креативность (0 = точный, 1 = творческий)
        "max_tokens": 2000         # Максимальная длина ответа
    }

    try:
        # ====== ОТПРАВЛЯЕМ ЗАПРОС В OPENROUTER ======
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=60  # Таймаут 60 секунд
        )

        # Проверяем, что запрос успешен (код 200)
        response.raise_for_status()

        # Парсим JSON-ответ
        data = response.json()

        # Достаём текст ответа модели
        answer = data['choices'][0]['message']['content']

        # Проверяем, что ответ не пустой
        if not answer or not answer.strip():
            return "Не получилось сформировать ответ. Попробуй переформулировать вопрос."

        # ====== СОХРАНЯЕМ В ИСТОРИЮ ======
        # Сохраняем сообщение пользователя и ответ бота в БД,
        # чтобы при следующем сообщении модель помнила контекст
        save_message(vk_user_id, "user", user_text)
        save_message(vk_user_id, "assistant", answer.strip())

        return answer.strip()

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при обращении к OpenRouter: {e}")
        # Пытаемся вывести подробности ошибки
        try:
            print(f"Ответ сервера: {response.text}")
        except Exception:
            pass
        return "Произошла ошибка при обработке запроса. Попробуй позже."


def reset_conversation(vk_user_id: int) -> None:
    """
    Полный сброс разговора: удаляет ID и очищает историю.
    Вызывается по команде /reset
    """
    clear_conversation_history(vk_user_id)