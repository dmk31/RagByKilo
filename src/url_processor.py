# -*- coding: utf-8 -*-
"""
Модуль для обработки URL и извлечения контента веб-страниц.

Этот модуль предоставляет классы для извлечения текстового контента
из веб-страниц, разбиения его на chunks оптимизированные для русского
языка, и интеграции с ChromaDB через ChromaDBManager.
"""

import hashlib
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter

from .chroma_manager import ChromaDBManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class WebContentExtractor:
    """
    Класс для извлечения и очистки контента из HTML-страниц.
    
    Предоставляет методы для получения веб-страниц, извлечения текста,
    метаданных и очистки контента для дальнейшей обработки.
    """

    def __init__(self, timeout: int = 30, user_agent: Optional[str] = None):
        """
        Инициализирует экстрактор веб-контента.

        Args:
            timeout (int): Таймаут для HTTP-запросов в секундах. Defaults to 30.
            user_agent (Optional[str]): User-Agent для HTTP-запросов. 
                Defaults to None (будет использован стандартный).
        """
        self.timeout = timeout
        self.session = requests.Session()
        
        # Установка User-Agent
        if user_agent:
            self.session.headers.update({'User-Agent': user_agent})
        else:
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

    def fetch_content(self, url: str) -> Tuple[str, int]:
        """
        Получает HTML-контент по указанному URL.

        Args:
            url (str): URL для получения контента.

        Returns:
            Tuple[str, int]: Кортеж (HTML-контент, статус-код).

        Raises:
            requests.RequestException: При ошибках HTTP-запроса.
            ValueError: При некорректном URL.
        """
        try:
            # Валидация URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Некорректный URL: {url}")

            logging.info(f"Получение контента с URL: {url}")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Проверка типа контента
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                logging.warning(f"URL не содержит HTML-контент: {content_type}")
            
            logging.info(f"Успешно получен контент. Размер: {len(response.text)} символов")
            return response.text, response.status_code

        except requests.exceptions.Timeout:
            logging.error(f"Таймаут при получении URL: {url}")
            raise
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка HTTP-запроса для URL {url}: {e}")
            raise
        except Exception as e:
            logging.error(f"Неожиданная ошибка при получении URL {url}: {e}")
            raise

    def extract_text(self, html: str) -> str:
        """
        Извлекает чистый текст из HTML-контента.

        Args:
            html (str): HTML-контент для обработки.

        Returns:
            str: Очищенный текстовый контент.
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Удаление ненужных элементов
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                               'aside', 'noscript', 'iframe', 'form']):
                element.decompose()
            
            # Извлечение текста
            text = soup.get_text(separator=' ', strip=True)
            
            # Очистка текста
            cleaned_text = self.clean_text(text)
            
            logging.info(f"Извлечен текст. Размер: {len(cleaned_text)} символов")
            return cleaned_text

        except Exception as e:
            logging.error(f"Ошибка при извлечении текста из HTML: {e}")
            raise

    def extract_metadata(self, html: str, url: str) -> Dict[str, Any]:
        """
        Извлекает метаданные из HTML-страницы.

        Args:
            html (str): HTML-контент.
            url (str): URL страницы.

        Returns:
            Dict[str, Any]: Словарь с метаданными.
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            metadata = {
                'url': url,
                'processed_date': datetime.now().isoformat(),
            }

            # Заголовок страницы
            title_tag = soup.find('title')
            metadata['title'] = title_tag.get_text(strip=True) if title_tag else ''

            # Meta description
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag:
                metadata['description'] = desc_tag.get('content', '').strip()
            else:
                # Попытка найти Open Graph description
                og_desc = soup.find('meta', attrs={'property': 'og:description'})
                metadata['description'] = og_desc.get('content', '').strip() if og_desc else ''

            # Meta keywords
            keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
            if keywords_tag:
                metadata['keywords'] = keywords_tag.get('content', '').strip()
            else:
                metadata['keywords'] = ''

            # Дополнительные метаданные
            author_tag = soup.find('meta', attrs={'name': 'author'})
            metadata['author'] = author_tag.get('content', '').strip() if author_tag else ''

            # Язык страницы
            html_tag = soup.find('html')
            metadata['language'] = html_tag.get('lang', '') if html_tag else ''

            logging.info(f"Извлечены метаданные для URL: {url}")
            return metadata

        except Exception as e:
            logging.error(f"Ошибка при извлечении метаданных: {e}")
            # Возвращаем базовые метаданные в случае ошибки
            return {
                'url': url,
                'processed_date': datetime.now().isoformat(),
                'title': '',
                'description': '',
                'keywords': '',
                'author': '',
                'language': ''
            }

    def clean_text(self, text: str) -> str:
        """
        Очищает и нормализует текст.

        Args:
            text (str): Исходный текст.

        Returns:
            str: Очищенный текст.
        """
        if not text:
            return ""

        # Удаление лишних пробелов и переносов строк
        text = re.sub(r'\s+', ' ', text)
        
        # Удаление повторяющихся знаков препинания
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        # Удаление лишних символов
        text = re.sub(r'[\r\n\t]+', ' ', text)
        
        return text.strip()


class URLChunker:
    """
    Класс для разбиения контента веб-страниц на chunks и интеграции с ChromaDB.
    
    Объединяет функциональность WebContentExtractor и ChromaDBManager
    для полного цикла обработки веб-контента.
    """

    def __init__(self, chroma_manager: ChromaDBManager, 
                 timeout: int = 30, user_agent: Optional[str] = None):
        """
        Инициализирует URLChunker.

        Args:
            chroma_manager (ChromaDBManager): Экземпляр менеджера ChromaDB.
            timeout (int): Таймаут для HTTP-запросов. Defaults to 30.
            user_agent (Optional[str]): User-Agent для запросов. Defaults to None.
        """
        self.chroma_manager = chroma_manager
        self.extractor = WebContentExtractor(timeout=timeout, user_agent=user_agent)
        
        # Настройка text splitter для русского языка
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=[
                "\n\n",  # Абзацы
                "\n",    # Строки
                ". ",    # Предложения
                "! ",    # Восклицательные предложения
                "? ",    # Вопросительные предложения
                "; ",    # Точка с запятой
                ", ",    # Запятые
                " ",     # Пробелы
                ""       # Символы
            ]
        )

    def process_url(self, url: str, collection_name: str, 
                   chunk_size: int = 1000, chunk_overlap: int = 200,
                   source_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Обрабатывает URL: извлекает контент, разбивает на chunks и сохраняет в ChromaDB.

        Args:
            url (str): URL для обработки.
            collection_name (str): Имя коллекции в ChromaDB.
            chunk_size (int): Размер chunk в символах. Defaults to 1000.
            chunk_overlap (int): Перекрытие между chunks. Defaults to 200.
            source_name (Optional[str]): Имя источника для метаданных. Defaults to None.

        Returns:
            Dict[str, Any]: Результат обработки с статистикой.

        Raises:
            Exception: При ошибках обработки URL или сохранения в БД.
        """
        try:
            start_time = time.time()
            logging.info(f"Начало обработки URL: {url}")

            # Настройка text splitter с переданными параметрами
            if chunk_size != 1000 or chunk_overlap != 200:
                self.text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    length_function=len,
                    separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]
                )

            # 1. Получение HTML-контента
            html_content, status_code = self.extractor.fetch_content(url)
            
            # 2. Извлечение метаданных
            metadata = self.extractor.extract_metadata(html_content, url)
            
            # 3. Извлечение текста
            text_content = self.extractor.extract_text(html_content)
            
            if not text_content.strip():
                logging.warning(f"Пустой текстовый контент для URL: {url}")
                return {
                    'success': False,
                    'error': 'Пустой текстовый контент',
                    'url': url,
                    'chunks_created': 0
                }

            # 4. Создание chunks
            chunks_data = self.create_chunks(text_content, metadata, source_name)
            
            # 5. Сохранение в ChromaDB
            self.save_to_chroma(chunks_data, collection_name)
            
            processing_time = time.time() - start_time
            
            result = {
                'success': True,
                'url': url,
                'chunks_created': len(chunks_data['chunks']),
                'total_characters': len(text_content),
                'processing_time': round(processing_time, 2),
                'metadata': metadata
            }
            
            logging.info(f"Успешно обработан URL {url}. "
                        f"Создано chunks: {len(chunks_data['chunks'])}, "
                        f"Время: {processing_time:.2f}с")
            
            return result

        except Exception as e:
            logging.error(f"Ошибка при обработке URL {url}: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url,
                'chunks_created': 0
            }

    def create_chunks(self, text: str, metadata: Dict[str, Any], 
                     source_name: Optional[str] = None) -> Dict[str, List]:
        """
        Разбивает текст на chunks с метаданными.

        Args:
            text (str): Текст для разбиения.
            metadata (Dict[str, Any]): Базовые метаданные.
            source_name (Optional[str]): Имя источника. Defaults to None.

        Returns:
            Dict[str, List]: Словарь с chunks, их ID и метаданными.
        """
        try:
            # Разбиение текста на chunks
            text_chunks = self.text_splitter.split_text(text)
            
            chunks = []
            chunk_ids = []
            chunk_metadatas = []
            
            for i, chunk in enumerate(text_chunks):
                # Генерация уникального ID для chunk
                chunk_id = hashlib.sha256(
                    f"{metadata['url']}_{i}_{chunk}".encode('utf-8')
                ).hexdigest()
                
                # Создание метаданных для chunk
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_index'] = i
                chunk_metadata['chunk_size'] = len(chunk)
                
                if source_name:
                    chunk_metadata['source'] = source_name
                
                chunks.append(chunk)
                chunk_ids.append(chunk_id)
                chunk_metadatas.append(chunk_metadata)
            
            logging.info(f"Создано {len(chunks)} chunks из текста размером {len(text)} символов")
            
            return {
                'chunks': chunks,
                'ids': chunk_ids,
                'metadatas': chunk_metadatas
            }

        except Exception as e:
            logging.error(f"Ошибка при создании chunks: {e}")
            raise

    def save_to_chroma(self, chunks_data: Dict[str, List], collection_name: str) -> None:
        """
        Сохраняет chunks в ChromaDB.

        Args:
            chunks_data (Dict[str, List]): Данные chunks для сохранения.
            collection_name (str): Имя коллекции.

        Raises:
            Exception: При ошибках сохранения в БД.
        """
        try:
            # Получение или создание коллекции
            collection = self.chroma_manager.get_or_create_collection(collection_name)
            
            # Сохранение chunks
            collection.upsert(
                documents=chunks_data['chunks'],
                ids=chunks_data['ids'],
                metadatas=chunks_data['metadatas']
            )
            
            logging.info(f"Успешно сохранено {len(chunks_data['chunks'])} chunks "
                        f"в коллекцию '{collection_name}'")

        except Exception as e:
            logging.error(f"Ошибка при сохранении chunks в коллекцию '{collection_name}': {e}")
            raise

    def process_multiple_urls(self, urls: List[str], collection_name: str,
                            chunk_size: int = 1000, chunk_overlap: int = 200,
                            source_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Обрабатывает несколько URL последовательно.

        Args:
            urls (List[str]): Список URL для обработки.
            collection_name (str): Имя коллекции в ChromaDB.
            chunk_size (int): Размер chunk. Defaults to 1000.
            chunk_overlap (int): Перекрытие chunks. Defaults to 200.
            source_name (Optional[str]): Имя источника. Defaults to None.

        Returns:
            List[Dict[str, Any]]: Список результатов обработки каждого URL.
        """
        results = []
        
        for i, url in enumerate(urls, 1):
            logging.info(f"Обработка URL {i}/{len(urls)}: {url}")
            
            try:
                result = self.process_url(
                    url=url,
                    collection_name=collection_name,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    source_name=source_name
                )
                results.append(result)
                
                # Небольшая пауза между запросами
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"Ошибка при обработке URL {url}: {e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'url': url,
                    'chunks_created': 0
                })
        
        successful = sum(1 for r in results if r['success'])
        total_chunks = sum(r['chunks_created'] for r in results)
        
        logging.info(f"Обработка завершена. Успешно: {successful}/{len(urls)} URL. "
                    f"Всего chunks: {total_chunks}")
        
        return results