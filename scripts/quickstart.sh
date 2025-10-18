#!/bin/bash
# SaaS Medical Tracker - Quickstart Script (Linux/macOS)
# This script sets up and runs the complete development environment

set -e  # Exit on any error

# Parse command line arguments
SKIP_BROWSER=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-browser)
            SKIP_BROWSER=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--skip-browser] [--verbose]"
            echo "  --skip-browser  Don't automatically open browser"
            echo "  --verbose       Enable verbose output"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Enable verbose output if requested
if [ "$VERBOSE" = true ]; then
    set -x
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 SaaS Medical Tracker - Quickstart Setup${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""

# Get script directory and root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get version of a command
get_command_version() {
    local cmd=$1
    local version_arg=${2:-"--version"}
    
    if command_exists "$cmd"; then
        $cmd $version_arg 2>&1 | head -n 1
    else
        echo "Command not found"
    fi
}

# Function to compare versions (simplified for major.minor comparison)
version_compare() {
    local version1=$1
    local version2=$2
    
    # Extract major and minor version numbers
    local v1_major=$(echo "$version1" | sed 's/[^0-9]*\([0-9]*\).*/\1/')
    local v1_minor=$(echo "$version1" | sed 's/[^0-9]*[0-9]*\.\([0-9]*\).*/\1/')
    local v2_major=$(echo "$version2" | sed 's/[^0-9]*\([0-9]*\).*/\1/')
    local v2_minor=$(echo "$version2" | sed 's/[^0-9]*[0-9]*\.\([0-9]*\).*/\1/')
    
    if [ "$v1_major" -gt "$v2_major" ]; then
        return 0  # version1 > version2
    elif [ "$v1_major" -eq "$v2_major" ] && [ "$v1_minor" -ge "$v2_minor" ]; then
        return 0  # version1 >= version2
    else
        return 1  # version1 < version2
    fi
}

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down development servers...${NC}"
    
    # Kill background processes
    if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        echo "Stopping backend server (PID: $BACKEND_PID)..."
        kill -TERM $BACKEND_PID 2>/dev/null || true
        # Wait for graceful shutdown
        for i in {1..5}; do
            if ! kill -0 $BACKEND_PID 2>/dev/null; then
                break
            fi
            sleep 1
        done
        # Force kill if still running
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill -KILL $BACKEND_PID 2>/dev/null || true
        fi
    fi
    
    if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "Stopping frontend server (PID: $FRONTEND_PID)..."
        kill -TERM $FRONTEND_PID 2>/dev/null || true
        # Wait for graceful shutdown
        for i in {1..5}; do
            if ! kill -0 $FRONTEND_PID 2>/dev/null; then
                break
            fi
            sleep 1
        done
        # Force kill if still running
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill -KILL $FRONTEND_PID 2>/dev/null || true
        fi
    fi
    
    # Kill any remaining processes on our ports
    if command_exists lsof; then
        echo "Cleaning up any remaining processes on ports 3000 and 8000..."
        lsof -ti:3000 | xargs -r kill -9 2>/dev/null || true
        lsof -ti:8000 | xargs -r kill -9 2>/dev/null || true
    elif command_exists netstat; then
        # Alternative cleanup for systems without lsof
        netstat -tulpn 2>/dev/null | grep ":3000\|:8000" | awk '{print $7}' | cut -d'/' -f1 | xargs -r kill -9 2>/dev/null || true
    fi
    
    cd "$ROOT_DIR"
    echo -e "${GREEN}✅ Development environment stopped${NC}"
    echo ""
    echo -e "${GREEN}🙏 Thank you for trying SaaS Medical Tracker!${NC}"
}

# Set up signal handlers
trap cleanup EXIT
trap cleanup INT
trap cleanup TERM

# Check prerequisites
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

# Check Python
if ! command_exists python3; then
    if command_exists python; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}❌ Python is not installed or not in PATH${NC}"
        echo -e "${YELLOW}   Please install Python 3.11+ from https://www.python.org/downloads/${NC}"
        exit 1
    fi
else
    PYTHON_CMD="python3"
fi

PYTHON_VERSION=$(get_command_version "$PYTHON_CMD")
echo "Python version output: $PYTHON_VERSION" >&2

if echo "$PYTHON_VERSION" | grep -qE "Python [0-9]+\.[0-9]+\.[0-9]+"; then
    if version_compare "$PYTHON_VERSION" "Python 3.11.0"; then
        echo -e "${GREEN}✅ Python: $PYTHON_VERSION${NC}"
    else
        echo -e "${RED}❌ Python 3.11+ is required, found: $PYTHON_VERSION${NC}"
        echo -e "${YELLOW}   Please upgrade Python from https://www.python.org/downloads/${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️ Could not determine Python version: $PYTHON_VERSION${NC}"
    echo -e "${YELLOW}   Proceeding anyway...${NC}"
fi

# Check Node.js
if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed or not in PATH${NC}"
    echo -e "${YELLOW}   Please install Node.js 18+ from https://nodejs.org/${NC}"
    exit 1
fi

NODE_VERSION=$(get_command_version "node")
echo "Node.js version output: $NODE_VERSION" >&2

if echo "$NODE_VERSION" | grep -qE "v[0-9]+\.[0-9]+\.[0-9]+"; then
    if version_compare "$NODE_VERSION" "v18.0.0"; then
        echo -e "${GREEN}✅ Node.js: $NODE_VERSION${NC}"
    else
        echo -e "${RED}❌ Node.js 18+ is required, found: $NODE_VERSION${NC}"
        echo -e "${YELLOW}   Please upgrade Node.js from https://nodejs.org/${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️ Could not determine Node.js version: $NODE_VERSION${NC}"
    echo -e "${YELLOW}   Proceeding anyway...${NC}"
fi

# Check npm
if ! command_exists npm; then
    echo -e "${RED}❌ npm is not installed${NC}"
    echo -e "${YELLOW}   Please install npm (usually comes with Node.js)${NC}"
    exit 1
fi

# Check Git (optional but recommended)
if command_exists git; then
    GIT_VERSION=$(get_command_version "git")
    echo -e "${GREEN}✅ Git: $GIT_VERSION${NC}"
else
    echo -e "${YELLOW}⚠️ Git not found - required for version control${NC}"
fi

# Check for pip
if ! command_exists pip3 && ! command_exists pip; then
    echo -e "${RED}❌ pip is not installed${NC}"
    echo -e "${YELLOW}   Please install pip (usually comes with Python)${NC}"
    exit 1
fi

if command_exists pip3; then
    PIP_CMD="pip3"
else
    PIP_CMD="pip"
fi

echo ""

# Setup Backend
echo -e "${BLUE}🐍 Setting up Backend Environment...${NC}"
BACKEND_DIR="$ROOT_DIR/backend"

if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ Backend directory not found: $BACKEND_DIR${NC}"
    exit 1
fi

cd "$BACKEND_DIR"
echo "Changed to backend directory: $BACKEND_DIR" >&2

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating Python virtual environment...${NC}"
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to create virtual environment${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
    source venv/bin/activate
    echo "Virtual environment activated" >&2
else
    echo -e "${RED}❌ Virtual environment activation script not found${NC}"
    exit 1
fi

# Install backend dependencies
echo -e "${YELLOW}📦 Installing backend dependencies...${NC}"
$PIP_CMD install -e ".[dev]"
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to install backend dependencies${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Backend dependencies installed${NC}"

# Run database migrations
echo -e "${YELLOW}🗄️ Setting up database...${NC}"
alembic upgrade head
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to run database migrations${NC}"
    echo -e "${YELLOW}   This might be normal for a fresh installation${NC}"
else
    echo -e "${GREEN}✅ Database migrations completed${NC}"
fi

# Setup Frontend
echo ""
echo -e "${BLUE}🌐 Setting up Frontend Environment...${NC}"
FRONTEND_DIR="$ROOT_DIR/frontend"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ Frontend directory not found: $FRONTEND_DIR${NC}"
    exit 1
fi

cd "$FRONTEND_DIR"
echo "Changed to frontend directory: $FRONTEND_DIR" >&2

# Install frontend dependencies
echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
npm install
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to install frontend dependencies${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Frontend dependencies installed${NC}"

# Generate TypeScript types from OpenAPI schema
CONTRACTS_DIR="$ROOT_DIR/contracts"
if [ -f "$CONTRACTS_DIR/openapi.yaml" ]; then
    echo -e "${YELLOW}🔄 Generating TypeScript types from OpenAPI schema...${NC}"
    npm run generate-types
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ TypeScript types generated${NC}"
    else
        echo -e "${YELLOW}⚠️ Failed to generate TypeScript types - continuing anyway${NC}"
    fi
fi

# Start Development Servers
echo ""
echo -e "${GREEN}🚀 Starting Development Servers...${NC}"
echo ""
echo -e "${CYAN}🔗 Access URLs:${NC}"
echo -e "${CYAN}  📱 Frontend:      http://localhost:3000${NC}"
echo -e "${CYAN}  🔧 Backend API:   http://localhost:8000${NC}"
echo -e "${CYAN}  📚 API Docs:      http://localhost:8000/docs${NC}"
echo -e "${CYAN}  ❤️ Health Check:  http://localhost:8000/health${NC}"
echo ""

# Start backend server in background
echo -e "${YELLOW}🔧 Starting backend server...${NC}"
cd "$BACKEND_DIR"
source venv/bin/activate

# Start backend in background and capture PID
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend server started with PID: $BACKEND_PID" >&2

# Wait a moment for backend to start
sleep 3

# Test backend health
if command_exists curl; then
    if curl -s --max-time 5 "http://localhost:8000/health" > /dev/null; then
        echo -e "${GREEN}✅ Backend server is running${NC}"
    else
        echo -e "${YELLOW}⚠️ Backend server may not be ready yet${NC}"
    fi
elif command_exists wget; then
    if wget --quiet --timeout=5 --tries=1 "http://localhost:8000/health" -O /dev/null; then
        echo -e "${GREEN}✅ Backend server is running${NC}"
    else
        echo -e "${YELLOW}⚠️ Backend server may not be ready yet${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ curl or wget not found - cannot test backend health${NC}"
fi

# Start frontend server in background
echo -e "${YELLOW}🌐 Starting frontend server...${NC}"
cd "$FRONTEND_DIR"

# Start frontend in background and capture PID
nohup npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend server started with PID: $FRONTEND_PID" >&2

# Wait for frontend to start
sleep 5

echo ""
echo -e "${GREEN}🎉 Development Environment Ready!${NC}"
echo ""
echo -e "${CYAN}📖 Quick Start Guide:${NC}"
echo -e "${WHITE}  1. Open http://localhost:3000 in your browser${NC}"
echo -e "${WHITE}  2. Create a test account or log in${NC}"
echo -e "${WHITE}  3. Try adding a medication in 'Medication Management'${NC}"
echo -e "${WHITE}  4. Log your first dose in 'Daily Logging'${NC}"
echo -e "${WHITE}  5. Explore the Health Passport features${NC}"
echo ""
echo -e "${YELLOW}🛑 Press Ctrl+C to stop all services${NC}"

# Open browser if not skipped
if [ "$SKIP_BROWSER" = false ]; then
    sleep 2
    if command_exists xdg-open; then
        xdg-open "http://localhost:3000" 2>/dev/null || echo -e "${YELLOW}⚠️ Could not open browser automatically${NC}"
    elif command_exists open; then
        open "http://localhost:3000" 2>/dev/null || echo -e "${YELLOW}⚠️ Could not open browser automatically${NC}"
    else
        echo -e "${YELLOW}⚠️ Could not open browser automatically${NC}"
        echo -e "${YELLOW}   Please navigate to http://localhost:3000 manually${NC}"
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}🌐 Opened application in default browser${NC}"
    fi
fi

# Monitor processes
echo ""
echo -e "${CYAN}📊 Monitoring servers... (Ctrl+C to stop)${NC}"

# Main monitoring loop
while true; do
    sleep 5
    
    # Check if backend process is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Backend server stopped unexpectedly${NC}"
        if [ -f "$BACKEND_DIR/backend.log" ]; then
            echo "Backend log (last 10 lines):"
            tail -n 10 "$BACKEND_DIR/backend.log"
        fi
        break
    fi
    
    # Check if frontend process is still running
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Frontend server stopped unexpectedly${NC}"
        if [ -f "$FRONTEND_DIR/frontend.log" ]; then
            echo "Frontend log (last 10 lines):"
            tail -n 10 "$FRONTEND_DIR/frontend.log"
        fi
        break
    fi
    
    # Optional: Check if servers are still responding
    # This is commented out to avoid too much network noise
    # if command_exists curl; then
    #     if ! curl -s --max-time 2 "http://localhost:3000" > /dev/null || \
    #        ! curl -s --max-time 2 "http://localhost:8000/health" > /dev/null; then
    #         echo -e "${YELLOW}⚠️ One or more servers may not be responding${NC}"
    #     fi
    # fi
done

# Cleanup will be handled by the trap
exit 0