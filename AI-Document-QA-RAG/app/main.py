from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.config import get_settings
from app.schemas import QuestionRequest, QuestionResponse
from app.services.document_service import (
    SUPPORTED_EXTENSIONS, extract_documents, new_document_id
)
from app.services.rag_service import get_rag_service

settings = get_settings()
settings.prepare_directories()

app = FastAPI(
    title=settings.app_name,
    description="Document question answering with RAG, LangChain, FastAPI and optional Kafka.",
    version="1.0.0",
)


@app.get("/")
def root():
    return {"message": settings.app_name, "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    original_name = Path(file.filename or "upload").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    document_id = new_document_id()
    destination = Path(settings.upload_dir) / f"{document_id}{suffix}"
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        if len(content) > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File exceeds the 20 MB limit.")
        destination.write_bytes(content)

        docs = extract_documents(destination, original_name)
        chunk_count = get_rag_service().add_documents(docs)

        try:
            from app.kafka.producer import publish_document_event
            kafka_published = publish_document_event(document_id, original_name, chunk_count)
        except Exception as exc:
            # Indexing succeeded; surface Kafka failure without discarding the index.
            kafka_published = False
            kafka_warning = str(exc)
        else:
            kafka_warning = None

        response = {
            "document_id": document_id,
            "filename": original_name,
            "extracted_characters": sum(len(doc.page_content) for doc in docs),
            "indexed_chunks": chunk_count,
            "kafka_event_published": kafka_published,
        }
        if kafka_warning:
            response["kafka_warning"] = kafka_warning
        return response
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        await file.close()


@app.post("/questions", response_model=QuestionResponse)
def ask_question(request: QuestionRequest):
    try:
        answer, sources = get_rag_service().ask(request.question, request.k)
        return QuestionResponse(answer=answer, sources=sources)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"RAG generation failed: {exc}") from exc
