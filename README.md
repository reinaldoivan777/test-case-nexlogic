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

## Improvement yang Sudah Dilakukan

Selain memenuhi tugas kandidat, implementasi ini juga menambahkan hardening berikut:

- Prompt instruction untuk LLM dikontrol penuh oleh backend. Backend tidak lagi mempercayai `prompt_template` yang dikirim dari graph frontend, sehingga caller tidak dapat mengganti instruksi RAG melalui payload API.
- Validasi graph diperketat untuk workflow `default`. Preview hanya menerima tepat empat node (`start`, `retrieval`, `llm`, `answer`) dan tepat tiga edge `Start → Retrieval → LLM → Answer`; extra node, duplicate node, extra edge, duplicate edge, cycle, atau `workflow_id` selain `default` akan ditolak.
- Batas ukuran input ditambahkan untuk mengurangi risiko abuse, biaya LLM berlebih, dan pertumbuhan data yang tidak terkendali:
  - request body maksimum `16 KB` melalui `MAX_CONTENT_LENGTH`;
  - `query` maksimum `500` karakter;
  - `workflow_id` maksimum `64` karakter;
  - context prompt maksimum `6000` karakter;
  - prompt final maksimum `8000` karakter.
- Error handling backend dinormalisasi. Payload terlalu besar mengembalikan error JSON `413`, input/graph tidak valid mengembalikan `400`, knowledge base yang tidak ditemukan mengembalikan `404`, dan provider embedding/LLM yang tidak tersedia mengembalikan `503`.
- `ValueError` dari `RagService.retrieve()` dipetakan menjadi `404` agar tidak bocor sebagai internal server error.
- Test backend diperluas untuk successful preview, history, prompt-template injection, validasi graph, batas query/request body, dan mapping retrieval error.

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
