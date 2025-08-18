# ChromaDBManager + URLProcessor

Комплексное решение для работы с векторной базой данных [ChromaDB](https://www.trychroma.com/) и обработки веб-контента. Включает в себя `ChromaDBManager` для управления векторной БД и `URLProcessor` для извлечения и индексации контента веб-страниц.

## Основные возможности

### ChromaDBManager
-   Простая инициализация клиента ChromaDB с использованием переменных окружения.
-   Удобные методы для создания, удаления и просмотра коллекций.
-   Автоматическое разбиение текстов на чанки с помощью `RecursiveCharacterTextSplitter` из `langchain`.
-   Генерация детерминированных ID для чанков на основе хэша, что обеспечивает идемпотентность при добавлении данных.
-   Поддержка `upsert` для атомарного добавления или обновления документов.
-   Возможность добавления метаданных и фильтрации по ним.
-   Высокоуровневые методы для семантического поиска.
-   Методы для удаления документов по ID или по источнику (через метаданные).
-   Полное логирование всех операций.

### URLProcessor
-   **Извлечение контента веб-страниц** с помощью `requests` и `BeautifulSoup`.
-   **Оптимизация для русского языка** - настроенные разделители для качественного разбиения текста.
-   **Извлечение метаданных** - заголовок, описание, ключевые слова, автор, язык страницы.
-   **Очистка и нормализация текста** - удаление лишних элементов, форматирование.
-   **Настраиваемое разбиение на chunks** - гибкие параметры `chunk_size` и `chunk_overlap`.
-   **Пакетная обработка URL** - возможность обработки нескольких страниц за один вызов.
-   **Интеграция с ChromaDB** - автоматическое сохранение обработанного контента.
-   **Обработка ошибок** - таймауты, валидация URL, логирование всех операций.

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

## Зависимости

Проект использует следующие основные библиотеки:
- `chromadb` - векторная база данных
- `langchain` - инструменты для работы с языковыми моделями
- `requests` - HTTP-клиент для получения веб-страниц
- `beautifulsoup4` - парсинг HTML-контента
- `lxml` - быстрый XML/HTML парсер
- `python-dotenv` - управление переменными окружения

## Примеры использования

### 1. Базовое использование ChromaDBManager

Основной функционал демонстрируется в файле `main.py`:

```python
from src.chroma_manager import ChromaDBManager

# Инициализация
db_manager = ChromaDBManager()

# Создание коллекции
collection_name = "my_collection"
db_manager.get_or_create_collection(name=collection_name)

# Добавление текстов
texts = ["Пример текста для индексации"]
metadatas = [{"source": "example"}]
db_manager.add_texts(
    collection_name=collection_name,
    texts=texts,
    metadatas=metadatas
)

# Поиск
results = db_manager.query_collection(
    collection_name=collection_name,
    query_texts=["поиск по тексту"],
    n_results=5
)
```

### 2. Обработка URL с URLProcessor

```python
from src.chroma_manager import ChromaDBManager
from src.url_processor import URLChunker

# Инициализация
db_manager = ChromaDBManager()
url_chunker = URLChunker(db_manager)

# Обработка одного URL
result = url_chunker.process_url(
    url="https://example.com/article",
    collection_name="web_content",
    chunk_size=1000,
    chunk_overlap=200,
    source_name="example_site"
)

print(f"Создано chunks: {result['chunks_created']}")
print(f"Заголовок: {result['metadata']['title']}")
```

### 3. Пакетная обработка URL

```python
# Обработка нескольких URL
urls = [
    "https://ru.wikipedia.org/wiki/Искусственный_интеллект",
    "https://ru.wikipedia.org/wiki/Машинное_обучение",
    "https://ru.wikipedia.org/wiki/Нейронная_сеть"
]

results = url_chunker.process_multiple_urls(
    urls=urls,
    collection_name="ai_articles",
    chunk_size=800,
    chunk_overlap=150
)

# Анализ результатов
successful = sum(1 for r in results if r['success'])
total_chunks = sum(r['chunks_created'] for r in results)
print(f"Обработано: {successful}/{len(urls)} URL")
print(f"Всего chunks: {total_chunks}")
```

### 4. Поиск по обработанному контенту

```python
# Семантический поиск по веб-контенту
search_results = db_manager.query_collection(
    collection_name="web_content",
    query_texts=["машинное обучение и нейронные сети"],
    n_results=5
)

for i, doc in enumerate(search_results['documents'][0]):
    metadata = search_results['metadatas'][0][i]
    distance = search_results['distances'][0][i]
    
    print(f"Результат {i+1}:")
    print(f"  URL: {metadata['url']}")
    print(f"  Заголовок: {metadata['title']}")
    print(f"  Релевантность: {1-distance:.3f}")
    print(f"  Текст: {doc[:150]}...")
```

## Запуск демонстраций

### Базовая демонстрация ChromaDBManager:
```bash
python main.py
```

### Полная демонстрация URLProcessor:
```bash
python demo_url_processor.py
```

## Особенности для русского языка

URLProcessor оптимизирован для работы с русским текстом:

- **Разделители для chunks**: `["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " "]`
- **Очистка текста**: удаление лишних пробелов, нормализация знаков препинания
- **Метаданные**: извлечение заголовков, описаний и ключевых слов на русском языке
- **Обработка кодировки**: корректная работа с UTF-8 контентом

## Структура метаданных

Каждый chunk содержит следующие метаданные:

```python
{
    "url": "исходный URL страницы",
    "title": "заголовок страницы",
    "description": "meta description",
    "keywords": "meta keywords",
    "author": "автор (если указан)",
    "language": "язык страницы",
    "processed_date": "дата обработки в ISO формате",
    "chunk_index": "номер chunk в документе",
    "chunk_size": "размер chunk в символах",
    "source": "имя источника (если указано)"
}
```

## API Reference

### WebContentExtractor

- `fetch_content(url)` - получение HTML по URL
- `extract_text(html)` - извлечение чистого текста
- `extract_metadata(html, url)` - извлечение метаданных
- `clean_text(text)` - очистка и нормализация текста

### URLChunker

- `process_url(url, collection_name, chunk_size, chunk_overlap, source_name)` - обработка одного URL
- `process_multiple_urls(urls, collection_name, ...)` - пакетная обработка URL
- `create_chunks(text, metadata, source_name)` - создание chunks с метаданными
- `save_to_chroma(chunks_data, collection_name)` - сохранение в ChromaDB

### ChromaDBManager

- `get_or_create_collection(name)` - создание/получение коллекции
- `add_texts(collection_name, texts, metadatas, ...)` - добавление текстов
- `query_collection(collection_name, query_texts, n_results, where)` - поиск
- `delete_by_ids(collection_name, ids)` - удаление по ID
- `delete_by_metadata(collection_name, where_filter)` - удаление по метаданным
- `count_items(collection_name)` - подсчет элементов
- `peek_collection(collection_name, n)` - просмотр элементов