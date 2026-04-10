import os
import chromadb

# Папка, где лежат текстовые файлы с базой знаний
KNOWLEDGE_DIR = "knowledge_files"

# Инициализируем ChromaDB — это локальная векторная база данных.
# Она умеет искать похожие по смыслу фрагменты текста.
# Аналог File Search от OpenAI, только работает локально.
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Создаём или открываем коллекцию (аналог хранилища файлов в OpenAI)
collection = chroma_client.get_or_create_collection(
    name="knowledge_base",
    metadata={"hnsw:space": "cosine"}  # Используем косинусное сходство для поиска
)


def split_text_into_chunks(text: str, chunk_size: int = 500) -> list[str]:
    """
    Разбивает длинный текст на маленькие кусочки (чанки).
    Это нужно, потому что модель лучше работает с небольшими
    релевантными фрагментами, а не с огромным текстом целиком.
    """
    paragraphs = text.split("\n\n")  # Разделяем по двойному переносу строки
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # Если добавление абзаца не превысит лимит — добавляем
        if len(current_chunk) + len(paragraph) + 2 <= chunk_size:
            current_chunk = f"{current_chunk}\n\n{paragraph}".strip()
        else:
            # Иначе сохраняем текущий чанк и начинаем новый
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = paragraph

    # Не забываем последний чанк
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def load_knowledge_base():
    """
    Загружает все текстовые файлы из папки knowledge_files
    и добавляет их в векторную базу данных.

    Аналог загрузки файлов в хранилище OpenAI.

    Запускать нужно ОДИН РАЗ или после обновления файлов.
    """

    # Проверяем, есть ли уже данные в базе
    if collection.count() > 0:
        print(f"База знаний уже загружена: {collection.count()} фрагментов")
        return

    # Создаём папку, если её нет
    if not os.path.exists(KNOWLEDGE_DIR):
        os.makedirs(KNOWLEDGE_DIR)
        print(f"Создана папка '{KNOWLEDGE_DIR}'. Положи туда текстовые файлы (.txt)")
        return

    all_chunks = []    # Все фрагменты текста
    all_ids = []       # Уникальные ID для каждого фрагмента
    all_metadata = []  # Метаданные (имя файла, номер фрагмента)
    chunk_counter = 0

    # Перебираем все файлы в папке
    for filename in os.listdir(KNOWLEDGE_DIR):
        if not filename.endswith(".txt"):
            continue  # Пропускаем не текстовые файлы

        filepath = os.path.join(KNOWLEDGE_DIR, filename)
        print(f"Загружаю файл: {filename}")

        # Читаем содержимое файла
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        # Разбиваем на чанки
        chunks = split_text_into_chunks(text)

        for i, chunk in enumerate(chunks):
            chunk_counter += 1
            all_chunks.append(chunk)
            all_ids.append(f"chunk_{chunk_counter}")
            all_metadata.append({
                "source": filename,      # Из какого файла
                "chunk_index": i         # Какой по счёту фрагмент
            })

    if not all_chunks:
        print("Не найдено текстовых файлов в папке knowledge_files/")
        return

    # Добавляем все фрагменты в векторную базу
    # ChromaDB автоматически создаст эмбеддинги (векторные представления)
    collection.add(
        documents=all_chunks,
        ids=all_ids,
        metadatas=all_metadata
    )

    print(f"Загружено {len(all_chunks)} фрагментов из {len(os.listdir(KNOWLEDGE_DIR))} файлов")


def search_knowledge(query: str, n_results: int = 3) -> str:
    """
    Ищет в базе знаний фрагменты, наиболее похожие на запрос пользователя.

    Аналог File Search от OpenAI.

    Возвращает найденные фрагменты в виде текста,
    который потом подставляется в промпт.
    """

    # Если база пустая — нечего искать
    if collection.count() == 0:
        return ""

    # Выполняем поиск по смыслу (семантический поиск)
    results = collection.query(
        query_texts=[query],     # Что ищем
        n_results=n_results      # Сколько результатов вернуть
    )

    # Собираем найденные фрагменты в один текст
    if not results["documents"] or not results["documents"][0]:
        return ""

    found_texts = []
    for i, doc in enumerate(results["documents"][0]):
        source = results["metadatas"][0][i].get("source", "неизвестно")
        found_texts.append(f"[Источник: {source}]\n{doc}")

    return "\n\n---\n\n".join(found_texts)