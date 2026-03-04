"""
Модуль для RAG (Retrieval-Augmented Generation) с использованием ChromaDB.
Позволяет загружать PDF учебники и искать в них релевантную информацию.
"""

import chromadb
from chromadb.config import Settings
import os
from pathlib import Path
from typing import List, Dict, Optional
import pymupdf4llm
import json

# Конфигурация ChromaDB
CHROMA_DB_PATH = Path(__file__).parent / "data" / "chroma_db"
CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)

# Клиент ChromaDB
client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory=str(CHROMA_DB_PATH),
    anonymized_telemetry=False
))


class RAGSystem:
    """Система для работы с учебниками и векторизацией текста."""
    
    def __init__(self):
        self.client = client
        self.textbooks: Dict[str, dict] = {}
        self._load_textbook_metadata()
    
    def _load_textbook_metadata(self):
        """Загружает метаданные учебников из файла."""
        metadata_file = CHROMA_DB_PATH / "textbooks.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                self.textbooks = json.load(f)
    
    def _save_textbook_metadata(self):
        """Сохраняет метаданные учебников."""
        metadata_file = CHROMA_DB_PATH / "textbooks.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.textbooks, f, ensure_ascii=False, indent=2)
    
    def add_textbook(self, pdf_path: str, subject: str, grade: int = 9) -> bool:
        """
        Добавляет учебник в базу знаний.
        
        Args:
            pdf_path: Путь до PDF файла
            subject: Название предмета (например, "Физика")
            grade: Класс (по умолчанию 9)
        
        Returns:
            True если успешно добавлено
        """
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                print(f"Файл не найден: {pdf_path}")
                return False
            
            if not pdf_path.suffix.lower() == '.pdf':
                print(f"Это не PDF файл: {pdf_path}")
                return False
            
            print(f"Обработка учебника: {pdf_path.name}")
            
            # Извлекаем текст из PDF с помощью pymupdf4llm
            # Это быстрый способ получить чистый Markdown из PDF
            try:
                doc = pymupdf4llm.to_markdown(str(pdf_path))
            except:
                # Если pymupdf4llm не работает, используем альтернативный метод
                import fitz
                pdf = fitz.open(pdf_path)
                doc = ""
                for page in pdf:
                    doc += page.get_text()
                pdf.close()
            
            # Разбиваем на чанки по 500 символов с перекрытием
            chunks = self._create_chunks(doc, chunk_size=500, overlap=100)
            
            # Создаем collection в ChromaDB
            collection_name = f"{subject.lower()}_{grade}"
            
            # Проверяем, существует ли уже такая collection
            try:
                collection = self.client.get_collection(name=collection_name)
                # Очищаем старые данные
                self.client.delete_collection(name=collection_name)
            except:
                pass
            
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"subject": subject, "grade": grade}
            )
            
            # Добавляем чанки в ChromaDB
            for i, chunk in enumerate(chunks):
                collection.add(
                    ids=[f"{pdf_path.stem}_chunk_{i}"],
                    documents=[chunk],
                    metadatas={
                        "source": pdf_path.name,
                        "subject": subject,
                        "grade": grade,
                        "chunk_index": i
                    }
                )
            
            # Сохраняем метаданные
            book_id = f"{subject}_{grade}_{pdf_path.stem}"
            self.textbooks[book_id] = {
                "name": pdf_path.name,
                "subject": subject,
                "grade": grade,
                "path": str(pdf_path),
                "chunks": len(chunks),
                "collection_name": collection_name
            }
            self._save_textbook_metadata()
            
            print(f"Учебник добавлен ({len(chunks)} чанков)")
            return True
        
        except Exception as e:
            print(f"Ошибка при добавлении учебника: {e}")
            return False
    
    def search(self, query: str, subject: Optional[str] = None, 
               grade: int = 9, top_k: int = 3) -> List[Dict]:
        """
        Ищет релевантные части учебника.
        
        Args:
            query: Поисковый запрос
            subject: Фильтр по предмету (опционально)
            grade: Класс (по умолчанию 9)
            top_k: Количество результатов
        
        Returns:
            Список результатов с текстом и метаданными
        """
        try:
            if subject:
                collection_name = f"{subject.lower()}_{grade}"
                try:
                    collection = self.client.get_collection(name=collection_name)
                except:
                    print(f"⚠️ Нет учебников по предмету {subject}")
                    return []
            else:
                # Ищем по всем доступным коллекциям
                collections = self.client.list_collections()
                if not collections:
                    print("⚠️ В базе нет учебников")
                    return []
                
                results = []
                for coll in collections:
                    collection = self.client.get_collection(name=coll.name)
                    result = collection.query(
                        query_texts=[query],
                        n_results=min(top_k, len(collection.count()))
                    )
                    if result and result['documents']:
                        for i, doc in enumerate(result['documents'][0]):
                            results.append({
                                'text': doc,
                                'metadata': result['metadatas'][0][i] if result['metadatas'] else {},
                                'distance': result['distances'][0][i] if result['distances'] else 0
                            })
                
                # Сортируем по релевантности
                results = sorted(results, key=lambda x: x.get('distance', 1))
                return results[:top_k]
            
            # Ищем в выбранной коллекции
            result = collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            if not result or not result['documents']:
                return []
            
            responses = []
            for i, doc in enumerate(result['documents'][0]):
                responses.append({
                    'text': doc,
                    'metadata': result['metadatas'][0][i] if result['metadatas'] else {},
                    'distance': result['distances'][0][i] if result['distances'] else 0
                })
            
            return responses
        
        except Exception as e:
            print(f"❌ Ошибка при поиске: {e}")
            return []
    
    def get_textbooks(self) -> Dict:
        """Возвращает список всех загруженных учебников."""
        return self.textbooks
    
    def delete_textbook(self, book_id: str) -> bool:
        """Удаляет учебник из базы."""
        try:
            if book_id not in self.textbooks:
                print(f"❌ Учебник не найден: {book_id}")
                return False
            
            collection_name = self.textbooks[book_id]['collection_name']
            self.client.delete_collection(name=collection_name)
            
            del self.textbooks[book_id]
            self._save_textbook_metadata()
            
            print(f"✅ Учебник удален")
            return True
        except Exception as e:
            print(f"❌ Ошибка при удалении: {e}")
            return False
    
    @staticmethod
    def _create_chunks(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """
        Разбивает текст на чанки с перекрытием.
        
        Args:
            text: Исходный текст
            chunk_size: Размер чанка
            overlap: Размер перекрытия
        
        Returns:
            Список чанков
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()
            
            if chunk:
                chunks.append(chunk)
            
            start += chunk_size - overlap
        
        return chunks


# Пример использования
if __name__ == "__main__":
    rag = RAGSystem()
    
    # Проверяем загруженные учебники
    books = rag.get_textbooks()
    if books:
        print(f"\n📚 Загруженные учебники ({len(books)}):")
        for book_id, info in books.items():
            print(f"  - {info['name']} ({info['subject']} {info['grade']} класс)")
    else:
        print("\n⚠️ Нет загруженных учебников")
    
    # Пример поиска
    # query = "квадратное уравнение"
    # results = rag.search(query, subject="Математика")
    # if results:
    #     print(f"\n📖 Найдено {len(results)} результатов:")
    #     for result in results:
    #         print(f"  {result['text'][:100]}...")
