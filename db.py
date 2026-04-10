import sqlite3
from contextlib import contextmanager
from typing import List, Dict

# Указываем путь к базе. Файл создастся автоматически и будет лежать рядом с нашим кодом.
DB_PATH = "bot.db"


# Создаем контекстного менеджера для подключения. Мы открываем соединение с базой данных, работаем с ним, а после завершения сохраняем изменения (делаем коммит) и закрываем соединение.
@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# Создаем таблицы.
# UserConversations - для хранения ID разговоров пользователей.
# MessageHistory - для хранения истории сообщений каждого пользователя.
def init_db():
    with get_conn() as conn:
        # Таблица для разговоров пользователей
        conn.execute(""" 
            CREATE TABLE IF NOT EXISTS user_conversations ( 
                vk_user_id INTEGER PRIMARY KEY, 
                conversation_id TEXT NOT NULL 
            ) 
        """)

        # Таблица для истории сообщений
        conn.execute(""" 
            CREATE TABLE IF NOT EXISTS message_history ( 
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vk_user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            ) 
        """)

        # Создаем индекс для быстрого поиска по vk_user_id
        conn.execute(""" 
            CREATE INDEX IF NOT EXISTS idx_vk_user_id 
            ON message_history(vk_user_id) 
        """)


def get_conversation_id(vk_user_id: int) -> str | None:
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT conversation_id FROM user_conversations WHERE vk_user_id = ?",
            (vk_user_id,)
        )
        row = cur.fetchone()
        return row[0] if row else None


def save_conversation_id(vk_user_id: int, conversation_id: str) -> None:
    with get_conn() as conn:
        conn.execute(""" 
            INSERT INTO user_conversations (vk_user_id, conversation_id) 
            VALUES (?, ?) 
            ON CONFLICT(vk_user_id) DO UPDATE SET conversation_id = excluded.conversation_id 
        """, (vk_user_id, conversation_id))


def delete_conversation_id(vk_user_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM user_conversations WHERE vk_user_id = ?",
            (vk_user_id,)
        )


# Новые функции для работы с историей сообщений

def save_message(vk_user_id: int, role: str, content: str) -> None:
    """
    Сохраняет сообщение в историю: role может быть "user" (сообщение от пользователя) или "assistant" (ответ бота)
    """
    with get_conn() as conn:
        conn.execute(""" 
            INSERT INTO message_history (vk_user_id, role, content) 
            VALUES (?, ?, ?) 
        """, (vk_user_id, role, content))


def get_conversation_history(vk_user_id: int, limit: int = 10) -> List[Dict[str, str]]:
    """
    Получает последние N сообщений из истории для контекста.
    Возвращает список в формате [{"role": "user", "content": "..."}, ...]
    """
    with get_conn() as conn:
        cur = conn.execute(""" 
            SELECT role, content FROM message_history 
            WHERE vk_user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ? 
        """, (vk_user_id, limit))

        rows = cur.fetchall()
        # Переворачиваем, чтобы сообщения шли в хронологическом порядке
        messages = [{"role": row[0], "content": row[1]} for row in reversed(rows)]
        return messages


def clear_conversation_history(vk_user_id: int) -> None:
    """
    Очищает всю историю сообщений пользователя.
    Полезно для команды "начать сначала" или "/reset"
    """
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM message_history WHERE vk_user_id = ?",
            (vk_user_id,)
        )


def get_message_count(vk_user_id: int) -> int:
    """
    Возвращает количество сообщений в истории пользователя.
    Может быть полезно для статистики или ограничений.
    """
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT COUNT(*) FROM message_history WHERE vk_user_id = ?",
            (vk_user_id,)
        )
        return cur.fetchone()[0]