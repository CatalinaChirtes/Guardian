#!/bin/bash

# GUARDIAN project runner
# usage:
#   ./run.sh setup    - install all dependencies and run DB migrations
#   ./run.sh start    - start both backend and frontend servers
#   ./run.sh stop     - stop both servers
#   ./run.sh restart  - stop then start
#   ./run.sh status   - check if servers are running

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_PID_FILE="$ROOT_DIR/.backend.pid"
FRONTEND_PID_FILE="$ROOT_DIR/.frontend.pid"

setup() {
    echo "=== Setting up backend ==="
    cd "$BACKEND_DIR"
    python3 -m venv venv 2>/dev/null
    source venv/bin/activate
    pip install -r requirements.txt

    if [ -f .env ]; then
        echo "=== Running database migrations ==="
        alembic upgrade head
    else
        echo "WARNING: backend/.env not found - skipping migrations"
        echo "Copy .env.example to .env and fill in your credentials"
    fi

    echo ""
    echo "=== Setting up frontend ==="
    cd "$FRONTEND_DIR"
    npm install

    echo ""
    echo "=== Setup complete ==="
}

start() {
    stop_quiet

    echo "=== Starting backend on :8000 ==="
    cd "$BACKEND_DIR"
    source venv/bin/activate
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    echo $! > "$BACKEND_PID_FILE"

    echo "=== Starting frontend on :4200 ==="
    cd "$FRONTEND_DIR"
    npx ng serve &
    echo $! > "$FRONTEND_PID_FILE"

    sleep 3
    echo ""
    echo "=== Both servers running ==="
    echo "  Frontend: http://localhost:4200"
    echo "  Backend:  http://localhost:8000"
    echo "  Stop with: ./run.sh stop"
}

start_prod() {
    stop_quiet

    echo "=== Starting backend (production, 4 workers) on :8000 ==="
    cd "$BACKEND_DIR"
    source venv/bin/activate
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 &
    echo $! > "$BACKEND_PID_FILE"

    echo "=== Starting frontend on :4200 ==="
    cd "$FRONTEND_DIR"
    npx ng serve &
    echo $! > "$FRONTEND_PID_FILE"

    sleep 3
    echo ""
    echo "=== Both servers running (production mode) ==="
    echo "  Frontend: http://localhost:4200"
    echo "  Backend:  http://localhost:8000 (4 workers)"
    echo "  Stop with: ./run.sh stop"
}

stop_quiet() {
    # kill by PID files
    for pidfile in "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE"; do
        if [ -f "$pidfile" ]; then
            kill "$(cat "$pidfile")" 2>/dev/null
            rm -f "$pidfile"
        fi
    done
    # kill by port as fallback
    lsof -ti :8000 | xargs kill 2>/dev/null
    lsof -ti :4200 | xargs kill 2>/dev/null
}

stop() {
    echo "=== Stopping servers ==="
    stop_quiet
    echo "Servers stopped."
}

status() {
    backend_pid=$(lsof -ti :8000 2>/dev/null)
    frontend_pid=$(lsof -ti :4200 2>/dev/null)

    if [ -n "$backend_pid" ]; then
        echo "Backend:  RUNNING (PID $backend_pid) on :8000"
    else
        echo "Backend:  STOPPED"
    fi

    if [ -n "$frontend_pid" ]; then
        echo "Frontend: RUNNING (PID $frontend_pid) on :4200"
    else
        echo "Frontend: STOPPED"
    fi
}

case "${1:-}" in
    setup)      setup ;;
    start)      start ;;
    start-prod) start_prod ;;
    stop)       stop ;;
    restart)    stop; start ;;
    status)     status ;;
    *)
        echo "Usage: ./run.sh {setup|start|start-prod|stop|restart|status}"
        echo ""
        echo "  setup      Install dependencies + run DB migrations"
        echo "  start      Start backend (:8000, dev mode with reload) and frontend (:4200)"
        echo "  start-prod Start backend (:8000, 4 workers) and frontend (:4200)"
        echo "  stop       Stop both servers"
        echo "  restart    Stop then start"
        echo "  status     Check if servers are running"
        ;;
esac
