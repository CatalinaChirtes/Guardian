# GUARDIAN: A Comparative Study On Programming Education Using Chatbots

Welcome to GUARDIAN, an LLM-powered programming assistant that helps students solve programming exercises by providing scaffolded hints instead of direct solutions to their problems, therefore fostering independent problem-solving. The goal is to aid learning by guiding students towards solutions, preventing over-reliance on direct answers.

This dissertation presents a unified pipeline for an AI Socratic Teaching Assistant that combines Socratic tutoring, RAG-grounded theory, static analysis, and frustration-triggered Parsons puzzles, capabilities previously studied in isolation. A three-level guardrail architecture enforces the Socratic constraint with a system prompt that instructs the LLM to provide only conceptual hints, a Code Police post-processor that detects and corrects code leakage using 14 regex patterns, and a Parsons puzzle fallback activated after repeated student failure. The pipeline supports five LLM models across four providers (Gemini, GPT, Claude, and Ollama) under identical guardrail conditions, enabling a controlled cross-model comparison.

We evaluated GUARDIAN through a local ablation experiment testing 400 model-configuration combinations across 20 test cases, and a one-week user study with 10 experienced practitioners. The ablation study showed that the Socratic system prompt alone reduces code leakage from 79% to 7% and increases pedagogical quality scores fivefold, while the Code Police eliminates the remaining leakage entirely. The three cloud models performed comparably (average scores of 7.07-7.27 out of 9.0), while local models scored approximately 30% lower but remained functional within the guardrail pipeline. The system achieved a mean SUS usability score of 91.0, well above the cross-industry benchmark of 68, and trust in AI increased while distrust decreased over the study period. Participants recognised the pedagogical value of the Socratic approach, with one noting: "Using this tutor you must learn, there is no shortcut to get through exercises".

## Poster Presentation

<img src="extras/Screenshots/Poster___GUARDIAN__A_Comparative_Study_On_Programming_Education_Using_Chatbots.png"/>

## Key Functionalities of the Application

### Chat with cloud LLM alternatives

Users can select their preferred model from a dropdown menu at the beginning of a session, and this per-session binding ensures that all messages within that conversation use the same model.

The quality difference between mid-tier and top-tier models was marginal for the Socratic tutoring task, as both tiers consistently followed the guardrail instructions, provided relevant hints, and avoided code leakage at similar rates. The cost difference, however, was substantial, which is why the mid-tier models were selected for deployment: gemini-2.5-flash, gpt-5.4-mini, and claude-haiku-4-5.

For local testing and comparison, five models were evaluated via Ollama, with Qwen 2.5 3B and Gemma 3 4B ultimately being selected, as they offered the best trade-off between response quality, latency, and reliability while comfortably fitting within the 16 GB memory of the test machine to provide an interactive tutoring experience.

<img src="extras/Screenshots/chat.png"/>

### Chat and code editor split view

The workspace provides a split-pane IDE layout with a Monaco code editor alongside a chat panel, having a sidebar menu that displays the pages and the entire history, making it easily accessible and easy to use. When a challenge session is solved, the exercise moves to the "Solved" tab on the practice page, and the student can restart it for additional practice if they choose. The layout is responsive, adapting from a mobile stacked view (30% editor, 70% chat) to a desktop side-by-side split (50/50).

<img src="extras/Screenshots/chat-editor.png"/>

### Socratic hint example

The core experience of GUARDIAN is a real-time chat where the student types a question, optionally attaches code from the built-in editor, and receives a Socratic hint rather than a direct answer. When code is attached, the student first sees an instant syntax-check banner (for example, "Python Syntax Error: line 3, column 12") before the tutor responds, so that obvious typos are caught immediately without waiting for the LLM. The tutor then replies with a conceptual hint that points the student in the right direction, by asking guiding questions like "What should happen when the loop counter reaches zero?", without ever writing code or giving away the solution. In the case where a student explicitly asks for the code, the tutor politely declines and redirects with a hint instead.

In challenge sessions, where the student is working on a specific exercise, the hints are targeted since the tutor knows the correct solution behind the scenes and can identify exactly where the student's approach diverges, but it never reveals or paraphrases the answer. The conversation maintains context across turns, so the student can build on previous exchanges without repeating themselves. Eventually, when the student's code is finally correct, the tutor congratulates them, the session is marked as solved, and the exercise appears under the "Solved" tab on the practice page, from where it can be restarted for additional practice.

As an additional safety net, every tutor response is automatically checked for accidental code leakage before being shown to the student. If code slips through, the system silently regenerates the response and if it slips through a second time, a safe fallback hint is displayed instead, ensuring the student never receives a direct code solution regardless of the model's behaviour.

<img src="extras/Screenshots/socratic-hint.png"/>

### Upload documents section

Beyond code debugging, students can ask conceptual questions grounded in their own course materials, so the student uploads lecture notes or textbook chapters (PDF or plain text, up to ten documents per account) through a dedicated panel in the workspace. Once the documents are uploaded, the system automatically detects when a question is conceptual rather than code-related and switches to Theory mode. In this mode, the response draws exclusively from the uploaded materials, and each answer includes source citations with filename and page number so the student can verify the information against the original document. If the uploaded materials do not cover the topic, the system says so rather than fabricating an answer, and falls back to general Socratic guidance.

The distinction between Socratic and Theory mode is seamless from the student's perspective as they simply type their question, and the system routes it to the appropriate mode based on whether code is present and whether relevant documents have been uploaded. The student sees a coloured badge on each response ("Socratic Hint" or "Theory") so they always know the source.

The RAG pipeline grounds theory responses in the student's own course materials, and demonstrates that the system can integrate domain-specific knowledge without retraining the underlying LLM. The user simply needs to attach a file in the dedicated "Documents" section, and then when asking a question, the LLM automatically looks in all the uploaded files for any matching resources.

<img src="extras/Screenshots/upload-curriculum.png"/>

### Theory response based on uploaded material

The retrieved chunks are formatted as numbered excerpts with source attribution and assembled into a context block within the system prompt. The prompt instructs the LLM to act as a "knowledgeable Professor," base answers exclusively on the provided excerpts, synthesise information across multiple excerpts when relevant, and clearly state when the excerpts do not contain enough information. Each response includes a sources summary listing the filenames and page numbers, which the frontend displays so students can verify the response against the original material.

<img src="extras/Screenshots/theory-mode.png"/>

### Practice page with programming exercises

The practice page provides access to a large corpus of programming exercises from the [CodeParrot APPS dataset](https://huggingface.co/datasets/codeparrot/apps), spanning three difficulty levels: introductory, interview, and competition. Students can filter by difficulty, browse paginated listings, or discover random challenges. Each exercise card shows a status badge (started, solved, or untouched) based on the student's previous sessions. Then the tabbed views (All, In Progress, Solved) with count badges give a quick overview of progress. By selecting an exercise a detailed modal opens with the full problem statement rendered with Markdown and mathematical notation, and context-aware action buttons: "Start" for a new attempt, "Continue" to resume an existing session, or "Retry" to start fresh after solving.

<img src="extras/Screenshots/practice-mode.png"/>
<img src="extras/Screenshots/continue-challenge.png"/>

### Challenge mode example with starter code

For challenge sessions, the pipeline checks whether the student's code is functionally correct by prompting the LLM at zero temperature to compare it against the reference solution. We implemented a hash-based deduplication optimisation so if the student's code has not changed since the last check (same hash), the solution evaluation is skipped to avoid redundant LLM calls.

<img src="extras/Screenshots/challenge-mode.png"/>

### Parsons Puzzle example

When a student has been struggling with a challenge for an extended period (ten or more unsuccessful attempts) and the system determines they are no longer making meaningful progress, the tutoring mode switches automatically, so instead of giving another hint, the student is presented with a Parsons puzzle. Here, the lines of the correct solution appear in a scrambled order, and the student rearranges them via drag-and-drop into the right sequence. This provides a structurally different learning activity that lets the student engage with the correct solution logic without simply being handed the answer. By doing a correct arrangement, the challenge is marked as solved, and the time spent and number of attempts on the puzzle are recorded for research analysis.

<img src="extras/Screenshots/parsons-puzzle.png"/>

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

## Frontend Environment

You also need to update the frontend environment files with your own Supabase credentials. Open the following files and replace the placeholder values:

- `frontend/src/environments/environment.ts` (for local development)
- `frontend/src/environments/environment.prod.ts` (for production deployment)

In both files, replace `YOUR_SUPABASE_URL` with your Supabase project URL and `YOUR_SUPABASE_ANON_KEY` with your Supabase publishable (anon) key. For the production file, also update the API and WebSocket URLs to point to your deployed backend.

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
