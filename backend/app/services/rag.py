import asyncio
import logging
import os
import threading
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class KnowledgeBase:
    def __init__(self):
        self.vector_store = None
        self.embeddings = None
        self.is_loaded = False
        self._lock = threading.RLock()
        self._index_mtime: float = 0.0

    def _ensure_embeddings(self):
        if self.embeddings is None:
            from langchain_community.embeddings import HuggingFaceEmbeddings

            self.embeddings = HuggingFaceEmbeddings(
                model_name=settings.embedding_model
            )

    def _save_index(self):
        index_path = settings.faiss_index_path
        os.makedirs(index_path, exist_ok=True)
        self.vector_store.save_local(index_path)
        self._update_mtime()
        try:
            from app.services.storage import upload_index
            upload_index(index_path)
        except Exception as e:
            logger.warning("Failed to upload FAISS index to Supabase Storage: %s", e)

    def _update_mtime(self):
        index_file = Path(settings.faiss_index_path) / "index.faiss"
        if index_file.exists():
            self._index_mtime = index_file.stat().st_mtime

    def _check_reload_needed(self) -> bool:
        index_file = Path(settings.faiss_index_path) / "index.faiss"
        if not index_file.exists():
            return False
        return index_file.stat().st_mtime > self._index_mtime

    def _clear_index(self):
        index_path = settings.faiss_index_path
        for f in Path(index_path).glob("*"):
            f.unlink()
        try:
            from app.services.storage import clear_index
            clear_index()
        except Exception as e:
            logger.warning("Failed to clear FAISS index from Supabase Storage: %s", e)

    def _ingest_file_sync(self, file_path: str, doc_id: str, filename: str) -> int:
        from langchain_community.document_loaders import PyPDFLoader, TextLoader
        from langchain_community.vectorstores import FAISS
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        self._ensure_embeddings()

        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding="utf-8")

        docs = loader.load()

        for doc in docs:
            doc.metadata["doc_id"] = doc_id
            doc.metadata["filename"] = filename

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        splits = splitter.split_documents(docs)

        with self._lock:
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(splits, self.embeddings)
            else:
                self.vector_store.add_documents(splits)

            self.is_loaded = True
            self._save_index()

        return len(splits)

    async def ingest_file(self, file_path: str, doc_id: str, filename: str) -> int:
        return await asyncio.to_thread(self._ingest_file_sync, file_path, doc_id, filename)

    def _search_sync(self, query: str, k: int = 6, score_threshold: float = 1.2, user_doc_ids: set[str] | None = None) -> list[dict]:
        if self._check_reload_needed():
            self._reload_index()
        if not self.vector_store:
            return []
        with self._lock:
            results = self.vector_store.similarity_search_with_score(query, k=k)
        filtered = []
        for doc, score in results:
            if score > score_threshold:
                continue
            if user_doc_ids is not None and doc.metadata.get("doc_id") not in user_doc_ids:
                continue
            filtered.append({
                "content": doc.page_content,
                "filename": doc.metadata.get("filename", "unknown"),
                "page": doc.metadata.get("page", None),
                "score": round(score, 3),
            })
        return filtered

    def _reload_index(self):
        try:
            from langchain_community.vectorstores import FAISS
        except ImportError:
            return
        index_path = settings.faiss_index_path
        self._ensure_embeddings()
        with self._lock:
            self.vector_store = FAISS.load_local(
                index_path,
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
            self.is_loaded = True
        self._update_mtime()
        logger.info("Reloaded FAISS index from disk (changed by another worker)")

    async def search(self, query: str, k: int = 6, user_doc_ids: set[str] | None = None) -> list[dict]:
        return await asyncio.to_thread(self._search_sync, query, k, 1.2, user_doc_ids)

    def _delete_document_sync(self, doc_id: str) -> None:
        if not self.vector_store:
            return

        with self._lock:
            docstore = self.vector_store.docstore
            index_to_id = self.vector_store.index_to_docstore_id

            ids_to_remove = []
            for idx, store_id in index_to_id.items():
                doc = docstore.search(store_id)
                if hasattr(doc, "metadata") and doc.metadata.get("doc_id") == doc_id:
                    ids_to_remove.append(store_id)

            if ids_to_remove:
                self.vector_store.delete(ids_to_remove)

                if self.vector_store.index.ntotal == 0:
                    self.vector_store = None
                    self.is_loaded = False
                    self._clear_index()
                else:
                    self._save_index()

    async def delete_document(self, doc_id: str) -> None:
        await asyncio.to_thread(self._delete_document_sync, doc_id)

    def _load_existing_index_sync(self):
        try:
            from langchain_community.vectorstores import FAISS
        except ImportError:
            return

        index_path = settings.faiss_index_path

        # try loading from local first
        if Path(index_path).exists() and any(Path(index_path).iterdir()):
            self._ensure_embeddings()
            with self._lock:
                self.vector_store = FAISS.load_local(
                    index_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
                self.is_loaded = True
            self._update_mtime()
            return

        # fall back to downloading from Supabase Storage
        try:
            from app.services.storage import download_index
            if download_index(index_path):
                self._ensure_embeddings()
                with self._lock:
                    self.vector_store = FAISS.load_local(
                        index_path,
                        self.embeddings,
                        allow_dangerous_deserialization=True,
                    )
                    self.is_loaded = True
                self._update_mtime()
                logger.info("Loaded FAISS index from Supabase Storage")
        except Exception as e:
            logger.warning("Failed to download FAISS index from Supabase Storage: %s", e)

    async def load_existing_index(self):
        await asyncio.to_thread(self._load_existing_index_sync)


rag_engine = KnowledgeBase()
