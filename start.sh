#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[FuzzPlanner]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[FuzzPlanner]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[FuzzPlanner]${NC} $1"
}

print_error() {
    echo -e "${RED}[FuzzPlanner]${NC} $1"
}

cleanup() {
    print_warning "Shutting down FuzzPlanner..."
    if [ ! -z "$BACKEND_PID" ]; then
        print_status "Stopping backend server (PID: $BACKEND_PID)"
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        print_status "Stopping frontend server (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    print_success "FuzzPlanner stopped successfully"
    exit 0
}

trap cleanup SIGINT SIGTERM

if [ ! -f "server_app.py" ] || [ ! -d "webapp" ]; then
    print_error "Please run this script from the FuzzPlanner root directory"
    exit 1
fi

print_status "Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

if ! command -v node &> /dev/null; then
    print_error "Node.js is required but not installed"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    print_error "npm is required but not installed"
    exit 1
fi

if [ ! -d "webapp/node_modules" ]; then
    print_status "Installing frontend dependencies..."
    cd webapp
    npm install
    cd ..
    print_success "Frontend dependencies installed"
fi

print_success "All dependencies are available"

print_status "Starting backend server on port 4000..."
python3 server_app.py &
BACKEND_PID=$!

sleep 2

if ! kill -0 $BACKEND_PID 2>/dev/null; then
    print_error "Failed to start backend server"
    exit 1
fi

print_success "Backend server started (PID: $BACKEND_PID)"

print_status "Starting frontend development server on port 3000..."
cd webapp
npm run dev &
FRONTEND_PID=$!
cd ..

sleep 3

if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    print_error "Failed to start frontend server"
    cleanup
    exit 1
fi

print_success "Frontend development server started (PID: $FRONTEND_PID)"

echo ""
print_success "🚀 FuzzPlanner is now running!"
echo ""
echo -e "${GREEN}Frontend:${NC} http://localhost:3000"
echo -e "${GREEN}Backend:${NC}  http://localhost:4000"
echo ""
print_warning "Press Ctrl+C to stop both servers"
echo ""

wait $BACKEND_PID $FRONTEND_PID