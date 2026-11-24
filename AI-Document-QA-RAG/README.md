# AI-Powered Document Question Answering System (RAG)

A rebuildable reference implementation of a document question-answering backend using **Python, FastAPI, LangChain, embeddings, FAISS, an Ollama-hosted LLM, and optional Apache Kafka**.

> **Important:** This is a newly reconstructed implementation based on the technologies and project description in the resume you shared. It is not the recovered original source code. The local vector store (FAISS), embedding model (Sentence Transformers), and Ollama integration are concrete implementation choices for this rebuild; verify them before describing them as part of your historical project.

## Features

- Upload PDF, DOCX, TXT, and Markdown documents.
- Extract text, split it into overlapping chunks, and generate embeddings.
- Persist document vectors locally with FAISS.
- Ask natural-language questions and retrieve relevant chunks.
- Generate grounded answers with an Ollama chat model through LangChain.
- FastAPI endpoints and interactive Swagger docs.
- Optional Kafka producer/consumer for document-ingestion events.

## Architecture

```text
Client
  |
  +-- POST /documents/upload --> FastAPI --> extract text --> chunk
  |                                                   |
  |                                                   v
  |                                          embedding model
  |                                                   |
  |                                                   v
  |                                             FAISS index
  |                                                   |
  +-- POST /questions -------------------------------+
                  |
                  v
           similarity search
                  |
                  v
        retrieved document chunks
                  |
                  v
           Ollama LLM + prompt
                  |
                  v
             grounded answer

Optional: upload endpoint --> Kafka topic --> consumer (event demonstration)
```

## Requirements

- Python 3.10+
- Ollama installed and running locally
- A chat model pulled in Ollama (default: `llama3.2`)
- Internet access on first run to download the embedding model
- Optional: Kafka broker, if enabling Kafka events

## Quick start

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

On Windows, copy `.env.example` to `.env` manually. Defaults use local Ollama and local FAISS storage.

### 4. Start Ollama

Install Ollama from https://ollama.com, then:

```bash
ollama pull llama3.2
ollama serve
```

If Ollama is already running as a background service, just run the `ollama pull` command.

### 5. Start the API

From the repository root:

```bash
uvicorn app.main:app --reload
```

Open:
- Swagger UI: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## API usage

### Upload a document

```bash
curl -X POST "http://127.0.0.1:8000/documents/upload" \
  -F "file=@sample.pdf"
```

Response includes the document ID, extracted character count, and number of indexed chunks.

### Ask a question

```bash
curl -X POST "http://127.0.0.1:8000/questions" \
  -H "Content-Type: application/json" \
  -d '{"question":"What are the main points in the document?","k":4}'
```

The response includes an answer and source metadata for the retrieved chunks. If the evidence is insufficient, the prompt instructs the model to say so.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Basic service information |
| GET | `/health` | Health check |
| POST | `/documents/upload` | Upload, parse, chunk, embed, and index a document |
| POST | `/questions` | Retrieve relevant chunks and generate an answer |

## Kafka (optional)

Kafka is disabled by default. To enable it:

1. Start a Kafka broker and create the topic configured by `KAFKA_TOPIC`.
2. Set `KAFKA_ENABLED=true` in `.env`.
3. Set `KAFKA_BOOTSTRAP_SERVERS` to your broker address.
4. Run the API and, in another terminal, start the consumer:

```bash
python -m app.kafka.consumer
```

The API publishes a JSON event after successful document indexing. The included consumer logs received events; extend its handler if you want downstream processing. Kafka is not required for the upload/query RAG flow.

## Configuration

See `.env.example`. Important settings:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server |
| `OLLAMA_MODEL` | `llama3.2` | Chat model |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Local embedding model |
| `VECTOR_STORE_DIR` | `data/faiss_index` | Persistent FAISS index |
| `CHUNK_SIZE` | `1000` | Chunk size |
| `CHUNK_OVERLAP` | `150` | Chunk overlap |
| `KAFKA_ENABLED` | `false` | Enable Kafka event publishing |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker |
| `KAFKA_TOPIC` | `document-ingested` | Event topic |

## Project structure

```text
AI-Document-QA-RAG/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_service.py
│   │   └── rag_service.py
│   └── kafka/
│       ├── __init__.py
│       ├── producer.py
│       └── consumer.py
├── data/                 # created at runtime; not committed
├── .env.example
├── .gitignore
└── requirements.txt
```

## Limitations and next steps

- This is a single-user starter implementation; add authentication and per-user document isolation before deployment.
- FAISS local persistence is suitable for a demo, not a complete multi-tenant production data layer.
- Ollama and the embedding model must be available locally.
- Add file-size limits, malware scanning, stronger content validation, rate limiting, and observability before exposing the API publicly.
- Consider background ingestion workers and Kafka retry/dead-letter handling for production workloads.

## Author

**S Aiman Zuha**  
B.Tech – Computer Science and Information Technology

Update this section with your actual GitHub and LinkedIn profile URLs.
