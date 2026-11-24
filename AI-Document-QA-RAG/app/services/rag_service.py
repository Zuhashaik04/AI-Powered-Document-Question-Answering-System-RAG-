from pathlib import Path
from threading import RLock

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate

from app.config import get_settings


class RAGService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._lock = RLock()
        self._embeddings = HuggingFaceEmbeddings(
            model_name=self.settings.embedding_model
        )
        self._vector_store: FAISS | None = None
        self._llm = ChatOllama(
            model=self.settings.ollama_model,
            base_url=self.settings.ollama_base_url,
            temperature=0,
        )
        self._prompt = ChatPromptTemplate.from_messages([
            ("system",
             "Answer using only the supplied context. If the context does not contain "
             "the answer, say that the uploaded documents do not provide enough information. "
             "Do not invent facts."),
            ("human", "Context:\n{context}\n\nQuestion: {question}"),
        ])
        self._load_existing_index()

    def _load_existing_index(self) -> None:
        path = Path(self.settings.vector_store_dir)
        if path.exists():
            try:
                self._vector_store = FAISS.load_local(
                    str(path), self._embeddings, allow_dangerous_deserialization=True
                )
            except Exception as exc:
                raise RuntimeError(
                    f"Could not load FAISS index at {path}: {exc}"
                ) from exc

    def add_documents(self, documents: list) -> int:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            add_start_index=True,
        )
        chunks = splitter.split_documents(documents)
        if not chunks:
            raise ValueError("Document did not produce any text chunks.")

        with self._lock:
            if self._vector_store is None:
                self._vector_store = FAISS.from_documents(chunks, self._embeddings)
            else:
                self._vector_store.add_documents(chunks)
            self._vector_store.save_local(self.settings.vector_store_dir)
        return len(chunks)

    def ask(self, question: str, k: int | None = None) -> tuple[str, list[dict]]:
        with self._lock:
            if self._vector_store is None:
                raise ValueError("No documents have been indexed yet. Upload a document first.")
            matches = self._vector_store.similarity_search(
                question, k=k or self.settings.retrieval_k
            )

        context_parts = []
        sources = []
        for doc in matches:
            context_parts.append(doc.page_content)
            sources.append({
                "source": str(doc.metadata.get("source", "unknown")),
                "page": doc.metadata.get("page"),
                "chunk": doc.page_content[:500],
            })

        chain = self._prompt | self._llm
        result = chain.invoke({
            "context": "\n\n---\n\n".join(context_parts),
            "question": question,
        })
        return str(result.content), sources


_rag_service: RAGService | None = None
_rag_lock = RLock()


def get_rag_service() -> RAGService:
    global _rag_service
    with _rag_lock:
        if _rag_service is None:
            _rag_service = RAGService()
        return _rag_service
