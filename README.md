# MiniDocs

A lightweight collaborative document editor (Google Docs inspired).

**Live URL:** https://minidocs-hkbt.onrender.com/

## Test users (no password)
- alice
- bob
- carol

Quick review flow: login as `alice` → create a doc → share with `bob` → logout → login as `bob` → see it under "Shared with me".
Note: free hosting sleeps after idle; first load can take 30-50 seconds.

## Features
- Create, rename, edit, auto-save and reopen documents
- Rich text: bold, italic, underline, H1/H2, bulleted and numbered lists
- File upload: `.txt`, `.md`, `.docx` (max 2 MB) becomes a new editable document. Other types are rejected with a clear message.
- Sharing: owner can share with another user. Dashboard separates "My documents" and "Shared with me"
- Persistence: SQLite, content stored as HTML so formatting is preserved

## Tech stack
FastAPI, SQLAlchemy, SQLite, React (Vite), TipTap editor, mammoth (docx import), markdown.

## Run locally

Backend:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Frontend (new terminal):
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

For a single-server build: `cd frontend && npm run build`, then run the backend. It serves `frontend/dist`.

## Tests
```bash
cd backend
pytest
```

## Known limitations
- Mocked auth (username only, no password)
- Shared users have edit access (no view-only role)
- SQLite on free hosting can reset on redeploy/restart
- No real-time collaboration