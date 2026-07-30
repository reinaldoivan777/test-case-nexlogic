# Nexlogic Mini RAG Workflow Builder

Assessment full-stack selama **60 menit** untuk mengimplementasikan integrasi RAG workflow pada baseline Nexlogic mini.

## Tujuan

Selesaikan alur berikut dari ReactFlow hingga preview:

```text
Start(query) → Knowledge Retrieval(knowledge base, top_k) → LLM → Answer
```

LLM disediakan evaluator melalui Ollama native API yang diekspos lewat ngrok. URL dan konfigurasi provider hanya tersedia pada `backend/.env`; frontend **tidak** boleh memanggil provider secara langsung.

## Yang Sudah Disediakan

- Flask, SQLite, CORS, route → service → model structure.
- Seed `Nexlogic Handbook` berisi lima chunk; embedding dokumen dibangkitkan dengan `nomic-embed-text:v1.5` melalui Ollama ngrok saat database pertama kali dibuat.
- Wrapper `EmbeddingService.generate_embedding()`, `RagService.retrieve()`, dan `LlmService.generate()`.
- React + TypeScript + ReactFlow canvas dengan graph RAG dasar.
- Daftar knowledge base, default workflow API, health endpoint, dan test fixture.

## Tugas Kandidat

1. Implementasikan update state konfigurasi pada `frontend/src/nodes/RetrievalNode.tsx`.
2. Implementasikan `POST /api/workflows/preview` di `backend/app/routes.py`, idealnya dengan service terpisah.
   - Validasi query, `knowledge_base_id`, `top_k` (1–5), dan graph Start → Retrieval → LLM → Answer.
   - Panggil retrieval, bangun prompt dengan context hasil retrieval, lalu panggil `LlmService.generate()`.
   - Simpan `WorkflowRun` ke SQLite.
   - Kembalikan answer, citation, trace, dan timestamp.
3. Implementasikan `GET /api/runs?workflow_id=default` untuk history terbaru terlebih dahulu.
4. Hubungkan tombol Preview di `frontend/src/App.tsx` ke API.
5. Render answer, citation, execution trace, history, serta empty/loading/error state.
6. Tambahkan minimal satu test backend untuk successful preview atau validation error.

## Kontrak API

### `POST /api/workflows/preview`

```json
{
  "workflow_id": "default",
  "query": "How does the RAG workflow work?",
  "nodes": [],
  "edges": []
}
```

Respons sukses `201`:

```json
{
  "id": "run-id",
  "workflow_id": "default",
  "query": "How does the RAG workflow work?",
  "answer": "...",
  "citations": [
    { "chunk_id": "...", "document_name": "Knowledge Retrieval.md", "score": 0.92 }
  ],
  "trace": [
    { "node_id": "start", "status": "succeeded" },
    { "node_id": "retrieval", "status": "succeeded", "retrieved_count": 3 },
    { "node_id": "llm", "status": "succeeded" },
    { "node_id": "answer", "status": "succeeded" }
  ],
  "created_at": "2026-01-01T00:00:00+00:00"
}
```

Gunakan format error berikut:

```json
{ "error": { "code": "validation_error", "message": "..." } }
```

- `400`: input atau konfigurasi graph tidak valid.
- `404`: knowledge base tidak ditemukan.
- `503`: provider LLM tidak tersedia.

## Menjalankan Baseline

### Prasyarat

- Python 3.11+
- Node.js 20+
- URL Ollama ngrok yang aktif dari evaluator

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Evaluator mengisi `OLLAMA_BASE_URL`, `OLLAMA_CHAT_MODEL`, dan `OLLAMA_EMBEDDING_MODEL=nomic-embed-text:v1.5` dalam `backend/.env`, lalu jalankan:

```bash
python run.py
```

Periksa provider tanpa mengekspos credential:

```bash
curl http://localhost:5050/api/preflight
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Buka `http://localhost:5174`.

### Test Backend

```bash
cd backend
pytest
```

## Batasan

- Jangan hardcode URL ngrok atau credential.
- Jangan menambah autentikasi, deployment, atau drag/drop node creator.
- Jangan mengganti `EmbeddingService` atau `RagService` dengan layanan cloud.
- Fokus pada kualitas integrasi, error handling, dan kode yang mudah dipelihara.
