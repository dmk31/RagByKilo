# -*- coding: utf-8 -*-
"""
Демонстрационный скрипт для использования ChromaDBManager.

Этот скрипт показывает основные операции с модулем:
- Инициализация менеджера
- Создание и управление коллекциями
- Добавление и индексация текстовых данных
- Выполнение семантического поиска
- Удаление данных из коллекции
"""

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
        logging.info(f"Используемая коллекция: '{collection_name}'")

        # Удаление старой коллекции, если она существует
        if collection_name in [c.name for c in db_manager.list_collections()]:
            logging.warning(f"Коллекция '{collection_name}' уже существует. Удаление...")
            db_manager.delete_collection(name=collection_name)

        # 3. Создание новой коллекции
        db_manager.get_or_create_collection(name=collection_name)

        # 4. Пример добавления текстов
        logging.info("--- Добавление текстов в коллекцию ---")
        docs_to_add = [
            "Векторные базы данных отлично подходят для семантического поиска.",
            "ChromaDB - это одна из популярных векторных баз данных.",
            "Langchain упрощает работу с языковыми моделями.",
            "Семантический поиск ищет по смыслу, а не по ключевым словам.",
        ]
        metadatas = [
            {"source": "doc1", "author": "AI"},
            {"source": "doc2", "author": "AI"},
            {"source": "doc3", "author": "Human"},
            {"source": "doc4", "author": "Human"},
        ]
        db_manager.add_texts(
            collection_name=collection_name,
            texts=docs_to_add,
            metadatas=metadatas,
            source_name="example_run"
        )

        # Проверка количества элементов
        count = db_manager.count_items(collection_name)
        logging.info(f"Количество элементов в коллекции: {count}")

        # 5. Пример семантического поиска
        logging.info("--- Выполнение семантического поиска ---")
        query = "Что такое векторные БД?"
        results = db_manager.query_collection(
            collection_name=collection_name,
            query_texts=[query],
            n_results=2
        )

        # 6. Пример вывода результатов
        if results and results.get("documents"):
            print("\nРезультаты поиска для запроса:", query)
            for i, doc in enumerate(results["documents"][0]):
                distance = results["distances"][0][i]
                metadata = results["metadatas"][0][i]
                print(f"  - Документ: '{doc}'")
                print(f"    - Расстояние: {distance:.4f}")
                print(f"    - Метаданные: {metadata}")
        else:
            print("\nНичего не найдено.")

        # 7. Пример удаления данных
        logging.info("--- Удаление данных из коллекции ---")
        # Удалим один документ по ID (ID генерируется из хэша контента)
        # Для этого нужно сначала получить ID. В реальном приложении ID надо сохранять.
        # Здесь для демонстрации мы его получим через peek.
        items = db_manager.peek_collection(collection_name, n=1)
        if items and items.get('ids'):
            doc_id_to_delete = items['ids'][0]
            logging.info(f"Удаление документа с ID: {doc_id_to_delete}")
            db_manager.delete_by_ids(collection_name, ids=[doc_id_to_delete])
            count_after_delete = db_manager.count_items(collection_name)
            logging.info(f"Количество элементов после удаления: {count_after_delete}")

        # Удаление всех данных от одного автора
        logging.info("Удаление всех документов от автора 'Human'")
        db_manager.delete_by_metadata(collection_name, where_filter={"author": "Human"})
        db_manager.delete_collection(name=collection_name)
        logging.info("Очистка завершена.")


    except Exception as e:
        logging.error(f"В ходе выполнения произошла ошибка: {e}")

    finally:
        logging.info("--- Демонстрация ChromaDBManager завершена ---")


if __name__ == "__main__":
    main()