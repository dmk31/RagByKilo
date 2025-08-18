# ChromaDBManager

`ChromaDBManager` — это легковесная объектно-ориентированная обертка для векторной базы данных [ChromaDB](https://www.trychroma.com/), написанная на Python. Она упрощает основные операции, такие как управление коллекциями, индексация текстовых данных, семантический поиск и удаление документов.

## Основные возможности

-   Простая инициализация клиента ChromaDB с использованием переменных окружения.
-   Удобные методы для создания, удаления и просмотра коллекций.
-   Автоматическое разбиение текстов на чанки с помощью `RecursiveCharacterTextSplitter` из `langchain`.
-   Генерация детерминированных ID для чанков на основе хэша, что обеспечивает идемпотентность при добавлении данных.
-   Поддержка `upsert` для атомарного добавления или обновления документов.
-   Возможность добавления метаданных и фильтрации по ним.
-   Высокоуровневые методы для семантического поиска.
-   Методы для удаления документов по ID или по источнику (через метаданные).
-   Полное логирование всех операций.

## Установка

1.  Клонируйте репозиторий:
    ```bash
    git clone <URL-репозитория>
    cd <имя-директории>
    ```

2.  Создайте и активируйте виртуальное окружение:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # для Linux/macOS
    # или
    .venv\Scripts\activate  # для Windows
    ```

3.  Установите зависимости:
    ```bash
    pip install -r requirements.txt
    ```

4.  Создайте файл `.env` в корне проекта и укажите путь для хранения базы данных:
    ```
    CHROMA_DB_PATH=./datasets_chroma
    ```

## Пример использования

Основной функционал демонстрируется в файле `main.py`.

```python
# main.py
import logging
from src.chroma_manager import ChromaDBManager

def main():
    """Главная функция для демонстрации работы ChromaDBManager."""
    logging.info("--- Запуск демонстрации ChromaDBManager ---")

    try:
        # 1. Создание экземпляра ChromaDBManager
        db_manager = ChromaDBManager()

        # 2. Определение имени коллекции
        collection_name = "my_test_collection"

        # 3. Создание новой коллекции
        db_manager.get_or_create_collection(name=collection_name)

        # 4. Добавление текстов
        docs_to_add = [
            "Векторные базы данных отлично подходят для семантического поиска.",
            "ChromaDB - это одна из популярных векторных баз данных.",
            "Langchain упрощает работу с языковыми моделями.",
        ]
        metadatas = [
            {"source": "doc1"},
            {"source": "doc2"},
            {"source": "doc3"},
        ]
        db_manager.add_texts(
            collection_name=collection_name,
            texts=docs_to_add,
            metadatas=metadatas,
        )

        # 5. Семантический поиск
        query = "Что такое векторные БД?"
        results = db_manager.query_collection(
            collection_name=collection_name,
            query_texts=[query],
            n_results=2
        )

        # 6. Вывод результатов
        print("\nРезультаты поиска для запроса:", query)
        if results and results.get("documents"):
            for doc, dist in zip(results["documents"][0], results["distances"][0]):
                print(f"  - Документ: '{doc}' (Расстояние: {dist:.4f})")

    finally:
        # Очистка
        db_manager.delete_collection(name=collection_name)
        logging.info("--- Демонстрация завершена ---")

if __name__ == "__main__":
    main()

```

### Запуск

Для запуска демонстрационного скрипта выполните команду:

```bash
python main.py