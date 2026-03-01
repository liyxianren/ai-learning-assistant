# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Learning Assistant - A multi-agent system for intelligent problem-solving that helps students analyze and solve homework problems. The system uses a pipeline architecture with three specialized agents:

1. **Image Recognition Agent**: Uses multimodal LLM (ChatGLM-4.6V) to extract text from problem images
2. **Problem Parsing Agent**: Analyzes problem type, subject, knowledge points, and difficulty
3. **Solution Agent**: Generates step-by-step solutions with detailed explanations

## Architecture

**Monorepo Structure**: Backend (Flask) + Frontend (Vanilla JS) deployed together via Docker with nginx reverse proxy.

### Backend (Flask)

- **Entry Point**: `backend/wsgi.py` → `backend/app/__init__.py:create_app()`
- **Blueprint-based routing**: Three main blueprints registered in `app/__init__.py`
  - `/api/auth` - User authentication (register, login)
  - `/api` - Core problem-solving APIs
  - `/api/history` - User history management
- **Service Layer**: `app/services/`
  - `pipeline_service.py` - Orchestrates the three-agent workflow
  - `ai_service.py` - Handles image recognition directly via multimodal API; delegates text ops to chatglm_service
  - `chatglm_service.py` - ChatGLM API integration (parsing, solving, streaming); contains heavy JSON normalization and field inference logic
- **Schemas**: `app/schemas/` - Marshmallow schemas for request validation (auth, history, problem)
- **Database**: SQLAlchemy with SQLite (default) or PostgreSQL
  - Models in `app/models/`: User, History
  - `db.create_all()` runs automatically on startup; `backend/migrations/` contains a one-time JSON→SQLite migration script
- **Extensions**: Initialized in `app/extensions.py` (db, jwt, cors, limiter)

### Frontend (Vanilla JavaScript)

- **Static files**: `frontend/index.html` (login), `frontend/app.html` (main app)
- **JavaScript**: `frontend/js/main.js` (app logic), `frontend/js/user.js` (auth)
- **No build step**: Direct HTML/CSS/JS served by nginx

### API Flow

```
POST /api/solve-problem
  ↓
pipeline_service.solve_problem()
  ↓
1. ai_service.recognize_image() [if image input]
2. ai_service.parse_problem()
3. ai_service.generate_solution()
  ↓
Save to History (if authenticated)
```

Streaming alternative: `POST /api/solve-stream` returns SSE stream.

## Development Commands

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:
- `CHATGLM_API_KEY` - Required for all AI operations
- `MULTIMODAL_MODEL` - Default: `glm-4.6v-flashx`
- `JWT_SECRET` - For user authentication

### Running Locally

**Backend only** (development):
```bash
cd backend
flask run --host=0.0.0.0 --port=5000
```

Or with Gunicorn (binds to port 3000 per `gunicorn.conf.py`):
```bash
cd backend
gunicorn -c gunicorn.conf.py wsgi:app
```

**Full stack** (Docker):
```bash
docker build -t ai-learning-assistant .
docker run -p 8080:8080 --env-file .env ai-learning-assistant
```

The Docker container runs both Flask (via Gunicorn) and nginx (serving frontend + reverse proxy) using supervisord.

### Database Migrations

```bash
cd backend
flask db init        # First time only
flask db migrate -m "description"
flask db upgrade
```

## Key Configuration

- **Rate Limiting**: Configured in `app/config.py` via `RATE_LIMIT_MAX_REQUESTS` and `RATE_LIMIT_WINDOW_MS`
- **CORS**: Single origin configured via `CORS_ORIGIN` (default: `http://localhost:8080`)
- **Request Timeout**: `REQUEST_TIMEOUT` (default: 120s) for AI API calls
- **Max Image Size**: `MAX_IMAGE_SIZE` (default: 5MB)

## AI Service Implementation

The `chatglm_service.py` implements three core methods:
- `recognize_image(image_base64)` - Extracts text from images using multimodal model
- `parse_problem(text)` - Returns structured JSON with problem analysis
- `generate_solution(text, parse_result)` - Returns detailed solution steps

All methods use the ChatGLM API with carefully crafted system prompts defined in the service file.

## Important Notes

- Frontend makes direct API calls to `/api/*` endpoints (proxied by nginx in production)
- Authentication is optional - anonymous users can solve problems but won't have history saved
- The system uses JWT tokens stored in localStorage for authenticated sessions
- All AI responses are in Chinese as this is an educational tool for Chinese students
