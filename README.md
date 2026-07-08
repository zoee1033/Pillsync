# PillSync
AI-powered medicine reminder and medication tracking platform for patients, caregivers, and administrators.

## Milestone 1 — Completed

This branch (`milestone-1`) contains the work for Milestone 1. Key features implemented in this milestone:

- Backend: FastAPI with PostgreSQL (SQLAlchemy)
	- User registration and login
	- JWT authentication
	- Password hashing (bcrypt)
	- Profile endpoints (fetch, update, change password)
	- Swagger/OpenAPI docs
- Frontend: React + Vite
	- Login, Register UI
	- Dashboard layout and protected routes
	- Profile and Settings pages
	- Axios integration with automatic Authorization header injection

## Local Setup

1. Create and activate virtual environment (backend)

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

2. Configure environment

- Copy `.env` with your DB and JWT secrets. Example keys:

```
DATABASE_URL=postgresql://user:password@localhost:5432/pillsync
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

3. Run backend

```bash
cd backend
python run.py
```

4. Run frontend

```bash
cd frontend
npm install
npm run dev
```

## How to verify authentication flow

1. Register a new user via the frontend or POST `/auth/register`.
2. Login via POST `/auth/login` and confirm you receive an `access_token`.
3. Use the token to access protected endpoints (e.g., GET `/profile/me`).
4. Change password via PUT `/profile/change-password`, then confirm:
	 - You can login with the new password.
	 - The old password no longer works.

## Notes

- This branch was created for Milestone 1 and is ready for review. Please open a Pull Request to merge `milestone-1` into `main` and request review from the project mentor.
- Do not commit secrets (keep `.env` in `.gitignore`).

---
If you need a tailored PR description, I can generate one to paste into GitHub.
