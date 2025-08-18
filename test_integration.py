# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки интеграции URLProcessor с ChromaDBManager.

Выполняет базовые тесты функциональности без использования реальных URL
для проверки корректности интеграции компонентов.
"""

import logging
import tempfile
import os
from src.chroma_manager import ChromaDBManager
from src.url_processor import WebContentExtractor, URLChunker

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def test_web_content_extractor():
    """Тест WebContentExtractor с примером HTML."""
    print("[ТЕСТ] Тестирование WebContentExtractor...")
    
    try:
        extractor = WebContentExtractor()
        
        # Тестовый HTML контент
        test_html = """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>Тестовая страница</title>
            <meta name="description" content="Описание тестовой страницы для проверки функциональности">
            <meta name="keywords" content="тест, html, парсинг">
            <meta name="author" content="Тестовый автор">
        </head>
        <body>
            <header>
                <nav>Навигация</nav>
            </header>
            <main>
                <h1>Заголовок статьи</h1>
                <p>Это первый абзац тестового контента. Он содержит важную информацию.</p>
                <p>Второй абзац продолжает тему. Здесь также есть полезная информация.</p>
                <script>console.log('Этот скрипт должен быть удален');</script>
                <p>Третий абзац завершает основной контент статьи.</p>
            </main>
            <footer>Подвал страницы</footer>
        </body>
        </html>
        """
        
        # Тест извлечения текста
        text = extractor.extract_text(test_html)
        print(f"[OK] Извлечен текст: {len(text)} символов")
        print(f"   Начало: {text[:100]}...")
        
        # Тест извлечения метаданных
        metadata = extractor.extract_metadata(test_html, "https://test.example.com")
        print(f"[OK] Извлечены метаданные:")
        print(f"   Заголовок: {metadata['title']}")
        print(f"   Описание: {metadata['description']}")
        print(f"   Ключевые слова: {metadata['keywords']}")
        print(f"   Автор: {metadata['author']}")
        print(f"   Язык: {metadata['language']}")
        
        # Тест очистки текста
        dirty_text = "Много    пробелов   и\n\n\nпереносов\t\tстрок!!!"
        clean_text = extractor.clean_text(dirty_text)
        print(f"[OK] Очистка текста: '{dirty_text}' -> '{clean_text}'")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка в WebContentExtractor: {e}")
        return False


def test_chroma_integration():
    """Тест интеграции с ChromaDBManager."""
    print("\n[ТЕСТ] Тестирование интеграции с ChromaDBManager...")
    
    try:
        # Создание временной директории для тестовой БД
        with tempfile.TemporaryDirectory() as temp_dir:
            # Временно изменяем переменную окружения
            original_path = os.getenv("CHROMA_DB_PATH")
            os.environ["CHROMA_DB_PATH"] = temp_dir
            
            try:
                # Инициализация компонентов
                db_manager = ChromaDBManager()
                url_chunker = URLChunker(db_manager)
                
                collection_name = "test_integration"
                
                # Тестовый текст для разбиения
                test_text = """
                Искусственный интеллект — это область компьютерных наук, которая занимается созданием 
                интеллектуальных машин, способных работать и реагировать как люди. Машинное обучение 
                является подмножеством искусственного интеллекта. Оно основано на идее, что системы 
                могут автоматически учиться и улучшаться на основе опыта без явного программирования.
                
                Глубокое обучение — это подмножество машинного обучения, которое имитирует работу 
                человеческого мозга в обработке данных и создании паттернов для принятия решений. 
                Нейронные сети являются основой глубокого обучения.
                """
                
                # Тестовые метаданные
                test_metadata = {
                    'url': 'https://test.example.com/ai-article',
                    'title': 'Статья об искусственном интеллекте',
                    'description': 'Обзор основных концепций ИИ',
                    'keywords': 'ИИ, машинное обучение, нейронные сети',
                    'author': 'Тестовый автор',
                    'language': 'ru',
                    'processed_date': '2024-01-01T00:00:00'
                }
                
                # Создание chunks
                chunks_data = url_chunker.create_chunks(test_text, test_metadata, "test_source")
                print(f"[OK] Создано chunks: {len(chunks_data['chunks'])}")
                
                # Сохранение в ChromaDB
                url_chunker.save_to_chroma(chunks_data, collection_name)
                print(f"[OK] Chunks сохранены в коллекцию '{collection_name}'")
                
                # Проверка количества элементов
                count = db_manager.count_items(collection_name)
                print(f"[OK] Элементов в коллекции: {count}")
                
                # Тест поиска
                search_results = db_manager.query_collection(
                    collection_name=collection_name,
                    query_texts=["что такое машинное обучение"],
                    n_results=2
                )
                
                if search_results and search_results.get('documents'):
                    print(f"[OK] Поиск работает: найдено {len(search_results['documents'][0])} результатов")
                    for i, doc in enumerate(search_results['documents'][0]):
                        distance = search_results['distances'][0][i]
                        print(f"   Результат {i+1}: релевантность {1-distance:.3f}")
                        print(f"   Текст: {doc[:80]}...")
                else:
                    print("[ERROR] Поиск не вернул результатов")
                    return False
                
                # Тест просмотра коллекции
                items = db_manager.peek_collection(collection_name, n=2)
                if items and items.get('documents'):
                    print(f"[OK] Просмотр коллекции: {len(items['documents'])} элементов")
                    for i, doc in enumerate(items['documents']):
                        metadata = items['metadatas'][i]
                        print(f"   Элемент {i+1}: chunk {metadata.get('chunk_index', 'N/A')}")
                
                # Очистка
                db_manager.delete_collection(collection_name)
                print(f"[OK] Коллекция '{collection_name}' удалена")
                
                return True
                
            finally:
                # Восстановление оригинального пути
                if original_path:
                    os.environ["CHROMA_DB_PATH"] = original_path
                else:
                    os.environ.pop("CHROMA_DB_PATH", None)
        
    except Exception as e:
        print(f"[ERROR] Ошибка в интеграции с ChromaDB: {e}")
        return False


def test_text_splitter_russian():
    """Тест разбиения русского текста на chunks."""
    print("\n[ТЕСТ] Тестирование разбиения русского текста...")
    
    try:
        db_manager = ChromaDBManager()
        url_chunker = URLChunker(db_manager)
        
        # Русский текст с различными разделителями
        russian_text = """
        Векторные базы данных представляют собой специализированные системы управления данными. 
        Они оптимизированы для хранения и поиска векторных представлений данных.
        
        Основные преимущества векторных БД:
        1. Быстрый семантический поиск
        2. Масштабируемость
        3. Поддержка различных типов данных
        
        ChromaDB является одной из популярных векторных баз данных! Она предоставляет простой API. 
        Разработчики могут легко интегрировать её в свои проекты? Да, это действительно так.
        
        Langchain упрощает работу с языковыми моделями; он предоставляет множество инструментов, 
        включая text splitters, которые помогают разбивать тексты на chunks оптимального размера.
        """
        
        # Тестирование с разными параметрами
        test_configs = [
            {"chunk_size": 200, "chunk_overlap": 50},
            {"chunk_size": 400, "chunk_overlap": 100},
            {"chunk_size": 600, "chunk_overlap": 150}
        ]
        
        for config in test_configs:
            # Настройка splitter
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            url_chunker.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=config["chunk_size"],
                chunk_overlap=config["chunk_overlap"],
                length_function=len,
                separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]
            )
            
            # Разбиение текста
            chunks = url_chunker.text_splitter.split_text(russian_text)
            
            print(f"[OK] Конфигурация {config}:")
            print(f"   Создано chunks: {len(chunks)}")
            print(f"   Размеры chunks: {[len(chunk) for chunk in chunks]}")
            
            # Проверка перекрытий
            if len(chunks) > 1:
                overlap_found = False
                for i in range(len(chunks) - 1):
                    chunk1_end = chunks[i][-50:]  # Последние 50 символов
                    chunk2_start = chunks[i + 1][:50]  # Первые 50 символов
                    
                    # Простая проверка на наличие общих слов
                    words1 = set(chunk1_end.split())
                    words2 = set(chunk2_start.split())
                    common_words = words1.intersection(words2)
                    
                    if common_words:
                        overlap_found = True
                        break
                
                print(f"   Перекрытие обнаружено: {'[OK]' if overlap_found else '[WARN]'}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка в тестировании text splitter: {e}")
        return False


def main():
    """Главная функция тестирования."""
    print("Запуск тестов интеграции URLProcessor")
    print("=" * 60)
    
    tests = [
        ("WebContentExtractor", test_web_content_extractor),
        ("Интеграция с ChromaDB", test_chroma_integration),
        ("Разбиение русского текста", test_text_splitter_russian)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n[ВЫПОЛНЕНИЕ] Тест: {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"[УСПЕХ] Тест '{test_name}' пройден успешно")
            else:
                print(f"[ПРОВАЛ] Тест '{test_name}' провален")
                
        except Exception as e:
            print(f"[КРИТИЧЕСКАЯ ОШИБКА] в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[ПРОЙДЕН]" if result else "[ПРОВАЛЕН]"
        print(f"{test_name}: {status}")
    
    print(f"\nОбщий результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("Все тесты пройдены успешно! Интеграция работает корректно.")
    else:
        print("Некоторые тесты провалены. Требуется дополнительная проверка.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)