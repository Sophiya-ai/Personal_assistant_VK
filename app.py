# код сервера для приема событий от ВКонтакте через механизм Callback API
#Callback API — это механизм, при котором VK отправляет HTTP-запросы на наш сервер,
# а сервер их принимает и реагирует.
# Без этих настроек мы не сможем получать сообщения от пользователя в сообществе.

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
#параметр, который нужен, чтобы вернуть простой текст (требование ВКонтакте)

# Импортируем настройки из конфига
from config import (
    validate_config,       # Функция проверки, что все переменные заполнены
    VK_CONFIRMATION_TOKEN, # Строка подтверждения для VK Callback API
    VK_SECRET,             # Секретный ключ для проверки, что запрос пришёл от VK
)

# Импортируем функции работы с базой данных
from db import (
    init_db,                      # Создание таблиц при запуске
    delete_conversation_id,       # Удаление ID разговора (для /reset)
    clear_conversation_history,   # Очистка истории сообщений (для /reset)
)

# Импортируем функцию общения с OpenRouter (бывший openai_client)
from llm_client import ask_openai

# Импортируем функцию отправки сообщений в VK
from vk_client import send_vk_message

# Создаём приложение FastAPI
app = FastAPI()

# Проверяем, что все переменные окружения/конфига заполнены
validate_config()

# Создаём таблицы в базе данных (если их ещё нет)
init_db()


def split_long_text(text: str, limit: int = 3500) -> list[str]:
    """
    VK не позволяет отправлять сообщения длиннее ~4096 символов.
    Эта функция разбивает длинный текст на части по абзацам,
    чтобы каждая часть не превышала limit символов.
    """

    # Если текст короткий — возвращаем как есть
    if len(text) <= limit:
        return [text]

    parts = []        # Список готовых частей
    current = ""      # Текущая собираемая часть

    # Разбиваем текст по абзацам (переносам строки)
    for paragraph in text.split("\n"):
        # Пробуем добавить абзац к текущей части
        candidate = f"{current}\n{paragraph}".strip() if current else paragraph

        if len(candidate) <= limit:
            # Если влезает — добавляем к текущей части
            current = candidate
        else:
            # Если не влезает — сохраняем текущую часть и начинаем новую
            if current:
                parts.append(current)

            if len(paragraph) <= limit:
                # Абзац влезает в одну часть — начинаем с него
                current = paragraph
            else:
                # Абзац слишком длинный — режем принудительно по символам
                for i in range(0, len(paragraph), limit):
                    parts.append(paragraph[i:i + limit])
                current = ""

    # Не забываем добавить последнюю собранную часть
    if current:
        parts.append(current)

    return parts


@app.post("/vk/callback", response_class=PlainTextResponse)
async def vk_callback(request: Request):
    """
    Главный обработчик запросов от VK Callback API.
    VK присылает сюда все события (новые сообщения, подтверждение и т.д.)
    """

    # Получаем JSON-данные из запроса
    data = await request.json()

    # Логируем событие для отладки (видно в консоли и в ngrok панели)
    print("VK EVENT:", data)

    # ====== ПРОВЕРКА БЕЗОПАСНОСТИ ======
    # Сверяем секретный ключ, чтобы убедиться, что запрос пришёл от VK,
    # а не от злоумышленника
    if data.get("secret") != VK_SECRET:
        return "forbidden"

    # ====== ПОДТВЕРЖДЕНИЕ СЕРВЕРА ======
    # При первичной настройке Callback API VK отправляет запрос типа "confirmation".
    # Мы должны ответить специальной строкой, чтобы VK подтвердил наш сервер.
    if data.get("type") == "confirmation":
        return VK_CONFIRMATION_TOKEN

    # ====== ОБРАБОТКА НОВОГО СООБЩЕНИЯ ======
    if data.get("type") == "message_new":
        # Достаём объект сообщения из данных
        message = data["object"]["message"]

        # Текст сообщения от пользователя (убираем пробелы по краям)
        user_text = (message.get("text") or "").strip()

        # peer_id — куда отправлять ответ (личка или беседа)
        peer_id = message.get("peer_id")

        # from_id — кто написал сообщение (ID пользователя VK)
        from_id = message.get("from_id")

        try:
            # --- Если пользователь отправил пустое сообщение (стикер, фото и т.д.) ---
            if not user_text:
                send_vk_message(peer_id, "Я пока умею работать только с текстовыми сообщениями.")
                return "ok"

            # --- Команда /reset — сброс контекста диалога ---
            if user_text.lower() == "/reset":
                # Удаляем ID разговора из базы
                delete_conversation_id(from_id)
                # Очищаем всю историю сообщений пользователя
                clear_conversation_history(from_id)
                send_vk_message(peer_id, "Контекст диалога сброшен. Можем начать заново!")
                return "ok"

            # --- Отправляем текст в OpenRouter и получаем ответ ---
            answer = ask_openai(from_id, user_text)

            # --- Разбиваем длинный ответ на части и отправляем по очереди ---
            for chunk in split_long_text(answer):
                send_vk_message(peer_id, chunk)

        except Exception as e:
            # Логируем ошибку в консоль
            print("ERROR:", e)
            try:
                # Пытаемся сообщить пользователю об ошибке
                send_vk_message(peer_id, "Ошибка сервера. Попробуй ещё раз.")
            except Exception as inner_e:
                # Если даже отправка ошибки не удалась — логируем
                print("VK SEND ERROR:", inner_e)

        return "ok"

    # Для всех остальных типов событий (вступление в группу и т.д.)
    # просто отвечаем "ok", чтобы VK не слал повторные запросы
    return "ok"