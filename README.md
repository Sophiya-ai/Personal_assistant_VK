# 📱 Personal_assistant_VK
**[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95.0-green)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)**

**Интеллектуальный помощник для VK на основе OpenRouter и FastAPI**

Бот отвечает на сообщения пользователей в VK, используя модель ИИ через [OpenRouter](https://openrouter.ai/).
Поддерживает контекст диалога, поиск по базе знаний и гибкую настройку промптов.

---

## 📌 Возможности

- **Ответы на сообщения** с использованием бесплатной GPT-модели (openai/gpt-oss-120b:free)
- **Контекст диалога** (бот помнит историю сообщений)
- **Векторный поиск по файлам** (локальная база знаний с ChromaDB)
- **Память диалогов** (SQLite)
- **Поддержка длинных сообщений** (автоматическое разбиение на части)
- **Команда `/reset`** для сброса контекста
- **Логирование** всех запросов для отладки

---

## 🛠️ Технологии

- FastAPI + Uvicorn               → Бэкенд
- OpenRouter REST                 → GPT-модель (бесплатно)
- ChromaDB                        → Векторный поиск по файлам (RAG)
- SQLite                          → База диалогов
- ngrok(для локальной разработки) → Туннелирование для VK
- VK Callback API                 → VK Интеграция

---

## 🚀 Быстрый старт

### ✨Предварительные требования

- Python 3.9+
- Учетная запись [OpenRouter](https://openrouter.ai/) (для API ключа)
- Сообщество VK с включенным Callback API

### 🔧Клонируйте репозиторий и установите зависимости

```bash
git clone https://github.com/Sophiya-ai/Personal_assistant_VK
cd Personal_assistant_VK

# Создай виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate     # Windows

pip install -r requirements.txt
```
_(Используйте python -m pip install -r requirements.txt, если pip не работает)_

### 🔧 Настройка
#### 1. Конфигурационный файл .env

```python
# OpenRouter API
OPENROUTER_API_KEY=your_openrouter_api_key      # Ключ с https://openrouter.ai/keys

# VK API
VK_GROUP_TOKEN=vk1.a.your_group_token           # Токен сообщества VK
VK_CONFIRMATION_TOKEN=your_confirmation_string  # Строка подтверждения из VK - сгенерируется автоматически в настройках VK Callback API
VK_SECRET=your_secret_key                       # Секретный ключ (опционально) - задайте любой для безопасности
VK_API_VERSION=5.199                            # Версия API ВКонтакте(опционально)
```
#### 2. Настройка VK Callback API
- Перейдите в __Управление сообществом__ → __Работа с API__ → __Callback API__
- Включите __Callback API__ и добавьте адрес:
```text
https://ваш-ngrok-url.ngrok-free.app/vk/callback
```
- Включите событие __"Входящие сообщения"__
- Скопируйте строку для подтверждения в `VK_CONFIRMATION_TOKEN`
- Нажмите __"Подтвердить"__

#### 3. База знаний
- Положите текстовые файлы (`.txt`) с информацией в папку `knowledge_files/`. 
- __При первом запуске__ — файлы автоматически загрузятся в ChromaDB.

--- 

## 🛠️  Запуск проекта (для разработки)
```bash
# 1. Бот
uvicorn app:app --reload --port 8000

# 2. ngrok (новый терминал)
ngrok http 8000
```

--- 

## 📂 Структура проекта
```text
📁 Personal_assistant_VK/
├── .env                  # Конфигурация (токены)
├── .gitignore            # Игнорируемые файлы (обязательно должен быть прописан `.env`)
├── app.py                # Основной сервер (FastAPI)
├── llm_client.py         # Логика общения с OpenRouter
├── config.py             # Настройки и валидация
├── db.py                 # Работа с SQLite
├── knowledge_base.py     # Векторный поиск (ChromaDB)
├── prompt.py             # Системный промпт для бота
├── vk_client.py          # Отправка сообщений в VK
├── requirements.txt      # Зависимости
├── 📁 knowledge_files/   # Файлы базы знаний (необходимые вам `.txt`)
└── README.md             # Файл описания проекта
└── bot.db                # База диалогов
```
--- 

## 📊 Сравнение подходов - почему REST API
|   Параметр   |	🌐 REST API| 	📦 SDK OpenAI|
|:--------------:|   :--------:   |       :---:|
|    💰 Цена	    |✅ Бесплатно	|❌ Платно|
   🤖 Модели	   |✅ 500+	|❌ Только GPT|
 📁 File Search |	✅ Локально |(ChromaDB)|	❌ Платный|
  ✍️ Prompt ID  |	✅ Свой промпт	|❌ Только OpenAI|
 ⚙️ Сложность	  |Средняя	|Лёгкая
  🎛️ Гибкость  |	✅ Максимум|	Ограниченная

--- 

✨ При разработке устанавливались следующие библиотеки
- 
```bash 
pip install -U fastapi uvicorn pydantic 
```
- __uvicorn__ - высокопроизводительный ASGI-сервер (Asynchronous Server Gateway Interface) для Python, предназначенный для запуска асинхронных веб-приложений, в том числе созданных с использованием FastAPI. Он построен на базе библиотек uvloop (быстрая реализация asyncio) и httptools (быстрый HTTP-парсер), что обеспечивает производительность, сравнимую с серверами на Go и Node.js
- __FastAPI__ - фреймворк для создания API
```bash 
pip install openai flask python-dotenv requests chromadb tiktoken
```
- __tiktoken__ - токенизатор для подсчета токенов
- __chromadb__ - векторная база данных

- затем все сохранялись в файл `requirements.txt`
```bash 
pip freeze > requirements.txt
```
--- 

## 🔍 Отладка проблем
### Логи не показываются
```text

1. Проверь ngrok: http://127.0.0.1:4040
2. Проверь порт: uvicorn --port 8000 + ngrok http 8000
3. Проверь URL: /vk/callback (с /vk/)
```
### Бот не отвечает
```text
1. config.py заполнен?
2. VK_GROUP_TOKEN имеет права messages? 
```

### File Search не работает
```text
1. knowledge_files/*.txt существуют?
2. Удали chroma_db/, перезапусти → автозагрузка
```
### Ошибка базы данных
```text
Удалите bot.db и перезапустите сервер
```
