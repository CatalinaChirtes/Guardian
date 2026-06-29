# GUARDIAN - AI Socratic Teaching Assistant

Welcome to GUARDIAN, an LLM-powered programming assistant that helps students solve programming exercises by providing scaffolded hints instead of direct solutions to their problems, therefore fostering independent problem-solving. The goal is to aid learning by guiding students towards solutions, preventing over-reliance on direct answers.

This app presents a unified pipeline for an AI Socratic Teaching Assistant that combines Socratic tutoring, RAG-grounded theory, static analysis, and frustration-triggered Parsons puzzles fallback.

## Prerequisites

Before starting, make sure you have the following installed on your machine:

- **Node.js** (v20 or later) - [Download here](https://nodejs.org/)
- **Python 3.12+** - [Download here](https://www.python.org/downloads/)
- **Git** - [Download here](https://git-scm.com/)

You will also need:

- A **Supabase** account (free tier works) - for the database and authentication
- At least one LLM API key (Gemini, OpenAI, or Anthropic) - for the AI tutor
- *(Optional)* **Ollama** installed locally - for local LLM models

## Quick Start

The fastest way to get everything running is with the provided `run.sh` script:

```bash
# 1. Clone the repository
git clone [url]
cd Guardian

# 2. Set up environment variables (see section below)

# 3. Install all dependencies and run database migrations
./run.sh setup

# 4. Start both servers
./run.sh start
```

The frontend will be available at **http://localhost:4200** and the backend at **http://localhost:8000**.

## Environment Variables

Before running `setup`, you need to create a `.env` file in the `backend/` folder. Create the file and fill in your credentials:

```bash
cd backend
touch .env
```

Add the following to `backend/.env`:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-role-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret

# database
DATABASE_URL=postgresql+asyncpg://postgres:password@host:5432/postgres

# LLM providers
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_LLM_PROVIDER=gemini

# CORS
CORS_ORIGINS=["http://localhost:4200"]

# HuggingFace
HF_TOKEN=your-huggingface-token

# Config flags
ENABLE_SOCRATIC_PROMPT=true
ENABLE_CODE_POLICE=true
ENABLE_RAG=true
```

## Manual Setup (Step by Step)

If you prefer to set things up manually instead of using `run.sh`:

### Backend

Open a terminal and navigate to the backend folder:

```bash
cd backend
```

Create a Python virtual environment and activate it:

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# or
venv\Scripts\activate           # Windows
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Run the database migrations (make sure your `.env` file is configured):

```bash
alembic upgrade head
```

Start the backend server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at **http://localhost:8000** and the API docs at **http://localhost:8000/docs**.

### Frontend

Open a **separate terminal** and navigate to the frontend folder:

```bash
cd frontend
```

Install the Node.js dependencies:

```bash
npm install
```

Start the development server:

```bash
npm start
```

The frontend will be available at **http://localhost:4200**.

## Using run.sh

The `run.sh` script provides convenient commands for managing both servers:

| Command | Description |
|---------|-------------|
| `./run.sh setup` | Install all dependencies (pip + npm) and run database migrations |
| `./run.sh start` | Start both backend (port 8000, with hot reload) and frontend (port 4200) |
| `./run.sh start-prod` | Start backend with 4 uvicorn workers (production mode) |
| `./run.sh stop` | Stop both servers |
| `./run.sh restart` | Stop and then start both servers |
| `./run.sh status` | Check if the servers are running |

## Project Structure

```
Guardian/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── routers/         # API endpoints (auth, chat, exercises, etc.)
│   │   ├── services/        # Business logic (tutor, RAG, code police, etc.)
│   │   │   └── llm/         # LLM provider implementations
│   │   ├── models/          # Database models and Pydantic schemas
│   │   ├── main.py          # Application entry point
│   │   └── config.py        # Environment configuration
│   ├── alembic/             # Database migrations
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Environment variables (create this)
├── extras/                  # Additional resources (initial experiments, Google Forms, data analysis files)
├── frontend/                # Angular 21 SPA
│   ├── src/app/
│   │   ├── core/            # Services, guards, interceptors
│   │   ├── features/        # Page components (workspace, practice, auth)
│   │   └── shared/          # Reusable components and pipes
│   └── package.json         # Node.js dependencies
├── .gitignore               # Files ignored at commit
├── README.md                # Project startup specifications
└── run.sh                   # Project runner script
```

## Accessing the Application

1. Open **http://localhost:4200** in your browser
2. Register with an `@e-uvt.ro` email address (or add your email to the `allowed_emails` table in Supabase)
3. Start a new chat session in the Workspace
4. Select your preferred LLM provider from the dropdown in the top bar
5. Type a question or paste code to get Socratic hints

## Running Tests

```bash
# Backend tests
cd backend
source venv/bin/activate
pytest tests/

# Frontend tests
cd frontend
npm test
```
