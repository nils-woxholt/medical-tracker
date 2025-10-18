#!/bin/bash
# Run full development environment
# Usage: ./scripts/run-dev.sh

echo "🚀 Starting SaaS Medical Tracker Development Environment"
echo "================================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down development servers..."
    
    # Kill background processes
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    
    # Kill any remaining processes on our ports
    pkill -f "uvicorn app.main:app" 2>/dev/null
    pkill -f "next dev" 2>/dev/null
    
    echo "✅ Development environment stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.11+ is required but not found"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '3\.[0-9]+')
if [[ "$PYTHON_VERSION" < "3.11" ]]; then
    echo "❌ Python 3.11+ is required, found $PYTHON_VERSION"
    exit 1
fi
echo "✅ Python: $(python3 --version)"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 18+ is required but not found"
    exit 1
fi

NODE_VERSION=$(node --version | grep -oE '[0-9]+' | head -1)
if [[ "$NODE_VERSION" -lt 18 ]]; then
    echo "❌ Node.js 18+ is required, found v$NODE_VERSION"
    exit 1
fi
echo "✅ Node.js: $(node --version)"

# Setup backend
echo "🐍 Setting up backend..."
BACKEND_DIR="$ROOT_DIR/backend"
cd "$BACKEND_DIR"

# Check if virtual environment exists
if [ ! -f "venv/bin/activate" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "📦 Installing backend dependencies..."
source venv/bin/activate
pip install -e ".[dev]"

# Run database migrations
echo "🗄️ Running database migrations..."
alembic upgrade head

# Setup frontend
echo "🌐 Setting up frontend..."
FRONTEND_DIR="$ROOT_DIR/frontend"
cd "$FRONTEND_DIR"

# Install frontend dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
else
    echo "📦 Updating frontend dependencies..."
    npm install
fi

# Start services
echo "🚀 Starting development servers..."
echo ""
echo "🔗 Service URLs:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""

# Start backend in background
cd "$BACKEND_DIR"
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend in background  
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

echo "🎯 Development servers started!"
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for background processes
wait