# AI Workflow Note

## Tools used
- Claude (chat) for planning, boilerplate and debugging
- VS Code for development

## Where AI materially sped up my work
- Project plan and scope cuts for the 4-6 hour limit
- FastAPI + SQLAlchemy backend boilerplate and sharing logic
- TipTap editor wiring and toolbar
- Debugging setup issues (PowerShell execution policy, Node/Vite setup, Render build config)

## What I changed or rejected
- changed seeded users / UI text / styling
- Rejected `npm audit fix --force` because it could break dependency versions
- Switched deployment to a prebuilt `frontend/dist` because Render's Python environment has no Node
- Fixed git author config that showed the wrong contributor

## How I verified correctness
- Automated pytest: share flow (403 before share, 200 after, non-owner cannot re-share) and invalid upload rejection
- Manual tests: create, format, refresh persistence, .md upload, share with bob and verify on his account
- Tested on the live deployed URL, not only locally