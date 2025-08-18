# -*- coding: utf-8 -*-
"""
Простой тест URLProcessor для проверки основной функциональности.
"""

import logging
from src.chroma_manager import ChromaDBManager
from src.url_processor import URLChunker

# Настройка логирования
logging.basicConfig(level=logging.INFO)

def main():
    """Простой тест основной функциональности."""
    print("Простой тест URLProcessor")
    print("=" * 40)
    
    try:
        # Инициализация
        db_manager = ChromaDBManager()
        url_chunker = URLChunker(db_manager)
        
        collection_name = "simple_test"
        
        # Удаление старой коллекции если есть
        existing = [c.name for c in db_manager.list_collections()]
        if collection_name in existing:
            db_manager.delete_collection(collection_name)
            print("Старая коллекция удалена")
        
        # Тестовый текст (имитация контента веб-страницы)
        test_text = """
        Искусственный интеллект представляет собой область компьютерных наук.
        Машинное обучение является важной частью ИИ.
        Нейронные сети используются для решения сложных задач.
        Глубокое обучение показывает отличные результаты в обработке изображений.
        """
        
        # Тестовые метаданные
        metadata = {
            'url': 'https://example.com/ai',
            'title': 'Статья об ИИ',
            'description': 'Обзор технологий ИИ',
            'keywords': 'ИИ, машинное обучение',
            'processed_date': '2024-01-01T00:00:00'
        }
        
        # Создание chunks
        chunks_data = url_chunker.create_chunks(test_text, metadata)
        print(f"Создано chunks: {len(chunks_data['chunks'])}")
        
        # Сохранение в ChromaDB
        url_chunker.save_to_chroma(chunks_data, collection_name)
        print("Chunks сохранены в ChromaDB")
        
        # Проверка количества
        count = db_manager.count_items(collection_name)
        print(f"Элементов в коллекции: {count}")
        
        # Поиск
        results = db_manager.query_collection(
            collection_name=collection_name,
            query_texts=["что такое машинное обучение"],
            n_results=2
        )
        
        if results and results.get('documents'):
            print(f"Найдено результатов: {len(results['documents'][0])}")
            for i, doc in enumerate(results['documents'][0]):
                print(f"  {i+1}. {doc[:60]}...")
        
        # Очистка
        db_manager.delete_collection(collection_name)
        print("Тест завершен успешно!")
        
        return True
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n[УСПЕХ] Модуль URLProcessor работает корректно!")
    else:
        print("\n[ОШИБКА] Есть проблемы с модулем")