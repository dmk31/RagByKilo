# -*- coding: utf-8 -*-
"""
Модуль для управления базой данных ChromaDB.

Этот модуль предоставляет класс ChromaDBManager, который является
объектно-ориентированной обёрткой для ChromaDB и упрощает работу с
векторными представлениями текстовых данных.
"""

import hashlib
import logging
import os
from typing import List, Optional, Dict, Any

import chromadb
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class ChromaDBManager:
    """
    Класс для управления векторной базой данных ChromaDB.

    Предоставляет высокоуровневые методы для инициализации клиента, управления
    коллекциями, индексации и поиска текстовых данных.
    """

    def __init__(self) -> None:
        """
        Инициализирует менеджер ChromaDB.

        Загружает переменные окружения из файла .env, инициализирует
        клиент ChromaDB (PersistentClient) с путем к базе данных из
        переменных окружения и обрабатывает возможные исключения.
        """
        try:
            load_dotenv()
            db_path = os.getenv("CHROMA_DB_PATH")
            if not db_path:
                raise ValueError(
                    "Переменная окружения CHROMA_DB_PATH не найдена. "
                    "Укажите путь к базе данных в файле .env."
                )

            # Инициализация клиента ChromaDB
            self.client = chromadb.PersistentClient(path=db_path)
            logging.info(
                f"Клиент ChromaDB успешно инициализирован. Путь к БД: {db_path}"
            )

        except ValueError as ve:
            logging.error(f"Ошибка конфигурации: {ve}")
            raise
        except Exception as e:
            logging.error(f"Неожиданная ошибка при инициализации ChromaDBManager: {e}")
            raise

    def get_or_create_collection(
        self, name: str
    ) -> chromadb.Collection:
        """
        Возвращает существующую коллекцию или создает новую.

        Args:
            name (str): Имя коллекции.

        Returns:
            chromadb.Collection: Объект коллекции.
        """
        try:
            collection = self.client.get_or_create_collection(name=name)
            logging.info(f"Коллекция '{name}' успешно получена или создана.")
            return collection
        except Exception as e:
            logging.error(f"Ошибка при создании/получении коллекции '{name}': {e}")
            raise

    def delete_collection(self, name: str) -> None:
        """
        Удаляет коллекцию по имени.

        Args:
            name (str): Имя коллекции для удаления.
        """
        try:
            self.client.delete_collection(name=name)
            logging.info(f"Коллекция '{name}' успешно удалена.")
        except Exception as e:
            logging.error(f"Ошибка при удалении коллекции '{name}': {e}")
            raise

    def list_collections(self) -> List[chromadb.Collection]:
        """
        Возвращает список всех существующих коллекций.

        Returns:
            List[chromadb.Collection]: Список объектов коллекций.
        """
        try:
            collections = self.client.list_collections()
            logging.info(f"Получен список коллекций: {[c.name for c in collections]}")
            return collections
        except Exception as e:
            logging.error(f"Ошибка при получении списка коллекций: {e}")
            raise

    def add_texts(
        self,
        collection_name: str,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        source_name: Optional[str] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        """
        Добавляет текстовые данные в указанную коллекцию.

        Разбивает тексты на чанки, генерирует для них детерминированные ID
        на основе хэша контента, проверяет на дубликаты и добавляет с
        помощью `upsert`.

        Args:
            collection_name (str): Имя целевой коллекции.
            texts (List[str]): Список текстов для индексации.
            metadatas (Optional[List[Dict[str, Any]]], optional):
                Список метаданных, соответствующий каждому тексту.
                Defaults to None.
            source_name (Optional[str], optional): Имя источника данных для
                отслеживания. Defaults to None.
            chunk_size (int, optional): Размер чанка. Defaults to 1000.
            chunk_overlap (int, optional): Перекрытие чанков. Defaults to 200.
        """
        try:
            collection = self.get_or_create_collection(name=collection_name)

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
            )

            chunks = []
            chunk_metadatas = []
            chunk_ids = []

            for i, text in enumerate(texts):
                # Разбиваем каждый текст на чанки
                split_chunks = text_splitter.split_text(text)
                for chunk in split_chunks:
                    # Генерация ID на основе хэша контента для идемпотентности
                    chunk_id = hashlib.sha256(chunk.encode("utf-8")).hexdigest()

                    chunks.append(chunk)
                    chunk_ids.append(chunk_id)

                    # Формирование метаданных
                    current_metadata = metadatas[i].copy() if metadatas and i < len(metadatas) else {}
                    if source_name:
                        current_metadata["source"] = source_name
                    chunk_metadatas.append(current_metadata)

            if not chunks:
                logging.warning("Нет чанков для добавления.")
                return

            # Использование upsert для идемпотентного добавления
            collection.upsert(
                documents=chunks,
                ids=chunk_ids,
                metadatas=chunk_metadatas,
            )
            logging.info(
                f"Успешно добавлено/обновлено {len(chunks)} чанков в коллекцию '{collection_name}'."
            )

        except Exception as e:
            logging.error(f"Ошибка при добавлении текстов в коллекцию '{collection_name}': {e}")
            raise

    def delete_by_ids(self, collection_name: str, ids: List[str]) -> None:
        """
        Удаляет документы из коллекции по списку их ID.

        Args:
            collection_name (str): Имя коллекции.
            ids (List[str]): Список ID документов для удаления.
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            collection.delete(ids=ids)
            logging.info(f"Успешно удалено {len(ids)} документов из коллекции '{collection_name}'.")
        except Exception as e:
            logging.error(f"Ошибка при удалении по ID из коллекции '{collection_name}': {e}")
            raise

    def delete_by_metadata(self, collection_name: str, where_filter: Dict[str, Any]) -> None:
        """
        Удаляет документы из коллекции на основе фильтра по метаданным.

        Args:
            collection_name (str): Имя коллекции.
            where_filter (Dict[str, Any]): Словарь для фильтрации.
                Например: `{"author": "Human"}`.
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            collection.delete(where=where_filter)
            logging.info(f"Успешно удалены документы по фильтру {where_filter} в коллекции '{collection_name}'.")
        except Exception as e:
            logging.error(
                f"Ошибка при удалении по метаданным из коллекции '{collection_name}': {e}"
            )
            raise

    def query_collection(
        self,
        collection_name: str,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Выполняет семантический поиск в коллекции.

        Args:
            collection_name (str): Имя коллекции для поиска.
            query_texts (List[str]): Список текстовых запросов.
            n_results (int, optional): Количество возвращаемых результатов.
                Defaults to 5.
            where (Optional[Dict[str, Any]], optional): Фильтр для метаданных.
                Defaults to None.

        Returns:
            Optional[Dict[str, Any]]: Словарь с результатами поиска или None.
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            query_params = {
                "query_texts": query_texts,
                "n_results": n_results,
            }
            if where:
                query_params["where"] = where

            results = collection.query(**query_params)
            logging.info(
                f"Выполнен поиск в коллекции '{collection_name}' с запросом: {query_texts}. "
                f"Найдено {len(results.get('documents', [[]])[0])} результатов."
            )
            return results
        except Exception as e:
            logging.error(f"Ошибка при поиске в коллекции '{collection_name}': {e}")
            raise

    def count_items(self, collection_name: str) -> Optional[int]:
        """
        Подсчитывает количество элементов в коллекции.

        Args:
            collection_name (str): Имя коллекции.

        Returns:
            Optional[int]: Количество элементов или None в случае ошибки.
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            count = collection.count()
            logging.info(f"В коллекции '{collection_name}' содержится {count} элементов.")
            return count
        except Exception as e:
            logging.error(f"Ошибка при подсчете элементов в коллекции '{collection_name}': {e}")
            raise

    def peek_collection(self, collection_name: str, n: int = 5) -> Optional[Dict[str, Any]]:
        """
        Возвращает первые n элементов из коллекции.

        Args:
            collection_name (str): Имя коллекции.
            n (int, optional): Количество элементов для просмотра. Defaults to 5.

        Returns:
            Optional[Dict[str, Any]]: Словарь с элементами или None в случае ошибки.
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            items = collection.peek(limit=n)
            logging.info(f"Просмотр первых {len(items.get('ids', []))} элементов из коллекции '{collection_name}'.")
            return items
        except Exception as e:
            logging.error(f"Ошибка при просмотре коллекции '{collection_name}': {e}")
            raise
