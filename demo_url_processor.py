# -*- coding: utf-8 -*-
"""
Демонстрационный скрипт для использования URLProcessor.

Этот скрипт показывает основные операции с модулем url_processor:
- Обработка одного URL
- Обработка нескольких URL
- Поиск по обработанному контенту
- Управление коллекциями
"""

import logging
from src.chroma_manager import ChromaDBManager
from src.url_processor import URLChunker

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def demo_single_url():
    """Демонстрация обработки одного URL."""
    logging.info("=== Демонстрация обработки одного URL ===")
    
    try:
        # Инициализация компонентов
        db_manager = ChromaDBManager()
        url_chunker = URLChunker(db_manager)
        
        collection_name = "web_content_demo"
        
        # Удаление старой коллекции если существует
        existing_collections = [c.name for c in db_manager.list_collections()]
        if collection_name in existing_collections:
            logging.info(f"Удаление существующей коллекции '{collection_name}'")
            db_manager.delete_collection(collection_name)
        
        # Тестовый URL (можно заменить на любой другой)
        test_url = "https://ru.wikipedia.org/wiki/Искусственный_интеллект"
        
        # Обработка URL
        result = url_chunker.process_url(
            url=test_url,
            collection_name=collection_name,
            chunk_size=800,  # Меньший размер для демонстрации
            chunk_overlap=150,
            source_name="wikipedia_demo"
        )
        
        # Вывод результатов
        if result['success']:
            print(f"\n✅ URL успешно обработан!")
            print(f"📄 URL: {result['url']}")
            print(f"📊 Создано chunks: {result['chunks_created']}")
            print(f"📝 Всего символов: {result['total_characters']}")
            print(f"⏱️ Время обработки: {result['processing_time']}с")
            print(f"📋 Заголовок: {result['metadata']['title']}")
            print(f"📝 Описание: {result['metadata']['description'][:100]}...")
        else:
            print(f"\n❌ Ошибка при обработке URL: {result['error']}")
            return
        
        # Проверка количества элементов в коллекции
        count = db_manager.count_items(collection_name)
        print(f"\n📊 Элементов в коллекции: {count}")
        
        # Демонстрация поиска
        print(f"\n=== Демонстрация поиска ===")
        search_queries = [
            "что такое искусственный интеллект",
            "машинное обучение",
            "нейронные сети"
        ]
        
        for query in search_queries:
            print(f"\n🔍 Поиск: '{query}'")
            search_results = db_manager.query_collection(
                collection_name=collection_name,
                query_texts=[query],
                n_results=2
            )
            
            if search_results and search_results.get('documents'):
                for i, doc in enumerate(search_results['documents'][0]):
                    distance = search_results['distances'][0][i]
                    metadata = search_results['metadatas'][0][i]
                    print(f"  📄 Результат {i+1}:")
                    print(f"     Текст: {doc[:150]}...")
                    print(f"     Релевантность: {1-distance:.3f}")
                    print(f"     Chunk: {metadata.get('chunk_index', 'N/A')}")
            else:
                print("  ❌ Ничего не найдено")
        
        # Просмотр нескольких элементов коллекции
        print(f"\n=== Просмотр элементов коллекции ===")
        items = db_manager.peek_collection(collection_name, n=3)
        if items and items.get('documents'):
            for i, doc in enumerate(items['documents']):
                metadata = items['metadatas'][i]
                print(f"\n📄 Элемент {i+1}:")
                print(f"   ID: {items['ids'][i][:16]}...")
                print(f"   Текст: {doc[:100]}...")
                print(f"   Chunk: {metadata.get('chunk_index', 'N/A')}")
                print(f"   Размер: {metadata.get('chunk_size', 'N/A')} символов")
        
    except Exception as e:
        logging.error(f"Ошибка в демонстрации: {e}")
        print(f"\n❌ Произошла ошибка: {e}")


def demo_multiple_urls():
    """Демонстрация обработки нескольких URL."""
    logging.info("=== Демонстрация обработки нескольких URL ===")
    
    try:
        # Инициализация компонентов
        db_manager = ChromaDBManager()
        url_chunker = URLChunker(db_manager)
        
        collection_name = "multi_url_demo"
        
        # Удаление старой коллекции если существует
        existing_collections = [c.name for c in db_manager.list_collections()]
        if collection_name in existing_collections:
            logging.info(f"Удаление существующей коллекции '{collection_name}'")
            db_manager.delete_collection(collection_name)
        
        # Список тестовых URL
        test_urls = [
            "https://ru.wikipedia.org/wiki/Машинное_обучение",
            "https://ru.wikipedia.org/wiki/Нейронная_сеть",
            "https://ru.wikipedia.org/wiki/Глубокое_обучение"
        ]
        
        print(f"\n📋 Обработка {len(test_urls)} URL...")
        
        # Обработка нескольких URL
        results = url_chunker.process_multiple_urls(
            urls=test_urls,
            collection_name=collection_name,
            chunk_size=600,
            chunk_overlap=100,
            source_name="wikipedia_ml_demo"
        )
        
        # Анализ результатов
        successful_count = sum(1 for r in results if r['success'])
        total_chunks = sum(r['chunks_created'] for r in results)
        
        print(f"\n📊 Результаты обработки:")
        print(f"   ✅ Успешно обработано: {successful_count}/{len(test_urls)} URL")
        print(f"   📄 Всего создано chunks: {total_chunks}")
        
        # Детальная информация по каждому URL
        for i, result in enumerate(results, 1):
            print(f"\n📄 URL {i}: {result['url']}")
            if result['success']:
                print(f"   ✅ Статус: Успешно")
                print(f"   📊 Chunks: {result['chunks_created']}")
                print(f"   📝 Символов: {result['total_characters']}")
                print(f"   ⏱️ Время: {result['processing_time']}с")
            else:
                print(f"   ❌ Статус: Ошибка - {result['error']}")
        
        # Общий поиск по всем обработанным документам
        if total_chunks > 0:
            print(f"\n=== Поиск по всем документам ===")
            search_query = "глубокое обучение и нейронные сети"
            print(f"🔍 Поиск: '{search_query}'")
            
            search_results = db_manager.query_collection(
                collection_name=collection_name,
                query_texts=[search_query],
                n_results=5
            )
            
            if search_results and search_results.get('documents'):
                print(f"📊 Найдено {len(search_results['documents'][0])} результатов:")
                for i, doc in enumerate(search_results['documents'][0]):
                    distance = search_results['distances'][0][i]
                    metadata = search_results['metadatas'][0][i]
                    print(f"\n   📄 Результат {i+1}:")
                    print(f"      URL: {metadata.get('url', 'N/A')}")
                    print(f"      Текст: {doc[:120]}...")
                    print(f"      Релевантность: {1-distance:.3f}")
        
        # Статистика коллекции
        final_count = db_manager.count_items(collection_name)
        print(f"\n📊 Итоговая статистика:")
        print(f"   📄 Элементов в коллекции: {final_count}")
        
    except Exception as e:
        logging.error(f"Ошибка в демонстрации множественных URL: {e}")
        print(f"\n❌ Произошла ошибка: {e}")


def cleanup_demo_collections():
    """Очистка демонстрационных коллекций."""
    logging.info("=== Очистка демонстрационных коллекций ===")
    
    try:
        db_manager = ChromaDBManager()
        demo_collections = ["web_content_demo", "multi_url_demo"]
        
        existing_collections = [c.name for c in db_manager.list_collections()]
        
        for collection_name in demo_collections:
            if collection_name in existing_collections:
                db_manager.delete_collection(collection_name)
                print(f"🗑️ Удалена коллекция: {collection_name}")
            else:
                print(f"ℹ️ Коллекция {collection_name} не найдена")
        
        print("✅ Очистка завершена")
        
    except Exception as e:
        logging.error(f"Ошибка при очистке: {e}")
        print(f"❌ Ошибка при очистке: {e}")


def main():
    """Главная функция демонстрации."""
    print("🚀 Демонстрация URLProcessor")
    print("=" * 50)
    
    try:
        # Демонстрация обработки одного URL
        demo_single_url()
        
        print("\n" + "=" * 50)
        input("Нажмите Enter для продолжения к демонстрации множественных URL...")
        
        # Демонстрация обработки нескольких URL
        demo_multiple_urls()
        
        print("\n" + "=" * 50)
        cleanup_choice = input("Удалить демонстрационные коллекции? (y/n): ").lower()
        
        if cleanup_choice in ['y', 'yes', 'да', 'д']:
            cleanup_demo_collections()
        else:
            print("ℹ️ Коллекции сохранены для дальнейшего изучения")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Демонстрация прервана пользователем")
    except Exception as e:
        logging.error(f"Критическая ошибка в демонстрации: {e}")
        print(f"\n❌ Критическая ошибка: {e}")
    
    finally:
        print("\n🏁 Демонстрация завершена")


if __name__ == "__main__":
    main()