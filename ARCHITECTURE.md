# Architecture Note

## Structure
React (Vite) frontend talks to a FastAPI REST backend. SQLite stores users, documents and shares. In production FastAPI also serves the built frontend, so there is one deployable service.

## What I prioritized and why
1. **Core document loop**: create, rename, edit, auto-save, reopen. This is the heart of the product.
2. **Sharing with real access checks**: enforced on the server (owner / shared / no access = 403), not just hidden in the UI. Covered by an automated test.
3. **Useful file upload**: .txt/.md/.docx become editable documents, with type and size validation.
4. **Deployability**: single service, simple setup, live URL.

## Key decisions
- **TipTap** instead of a custom editor: saves time, reliable formatting.
- **Content stored as HTML**: formatting survives refresh without a custom format.
- **Debounced auto-save (800 ms)** with a visible Saving / Saved / Save failed status.
- **Mocked auth** via `X-Username` header and seeded users. Keeps scope small while still demonstrating ownership and sharing logic.
- **SQLite** for zero-cost setup; `DB_URL` env var allows switching to Postgres.

## Deliberately deprioritized
Real-time collaboration, comments, version history, export, role-based permissions, real authentication.

## Tradeoffs and known issues
- Header-based auth is not secure; a real product needs JWT/sessions.
- Last write wins if two users edit at once.
- SQLite data may reset on free hosting.

## Next 2-4 hours
Postgres for durable storage, view/edit roles, JWT auth, PDF/Markdown export.