#!/bin/bash

# Etsy Seller Automaker Docker Runner
# This script helps you run the application in different modes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if .env file exists
check_env() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Please create one with your Etsy API credentials."
        print_status "You can copy from .env.example if available."
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  dev     - Run in development mode (separate frontend and backend containers)"
    echo "  prod    - Run in production mode (single container with built frontend)"
    echo "  local   - Run backend locally (not Docker Compose)"
    echo "  test    - Run tests in the backend container"
    echo "  stop    - Stop all containers"
    echo "  clean   - Stop and remove all containers and images"
    echo "  logs    - Show logs from running containers"
    echo "  help    - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev     # Start development environment"
    echo "  $0 prod    # Start production environment"
    echo "  $0 local   # Run backend locally"
    echo "  $0 test    # Run tests"
    echo "  $0 stop    # Stop all containers"
}

# Function to run development environment
run_dev() {
    print_status "Starting development environment..."
    check_docker
    check_env
    
    print_status "Building and starting containers..."
    docker-compose up --build -d
    
    print_success "Development environment started!"
    print_status "Frontend: http://localhost:3000"
    print_status "Backend:  http://localhost:3003"
    print_status "API Docs: http://localhost:3003/docs"
    echo ""
    print_status "To view logs: $0 logs"
    print_status "To stop: $0 stop"
}

# Function to run production environment
run_prod() {
    print_status "Starting production environment..."
    check_docker
    check_env
    
    print_status "Building and starting production container..."
    docker-compose -f docker-compose.prod.yml up --build -d
    
    print_success "Production environment started!"
    print_status "Application: http://localhost:3003"
    print_status "API Docs: http://localhost:3003/docs"
    echo ""
    print_status "To view logs: $0 logs"
    print_status "To stop: $0 stop"
}

# Function to run backend locally (not Docker Compose)
run_local() {
    print_status "Running backend locally (not Docker Compose)..."
    check_env
    if ! grep -q 'localhost' .env; then
        print_warning "Your .env DATABASE_URL does not use 'localhost'. Updating for local dev."
        sed -i '' 's/db/localhost/g' .env
        print_success ".env updated to use localhost."
    fi
    print_status "Make sure your local PostgreSQL is running and has a database named 'etsydb'."
    print_status "Starting backend with: python server/main.py"
    python3 server/main.py
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    check_docker
    
    # Check if backend container is running
    if docker-compose ps | grep -q "backend.*Up"; then
        print_status "Running tests in existing backend container..."
        docker-compose exec backend python -m pytest server/tests/ -v
    else
        print_status "Starting backend container for testing..."
        docker-compose up --build -d backend
        sleep 5  # Wait for container to be ready
        docker-compose exec backend python -m pytest server/tests/ -v
    fi
    
    print_success "Tests completed!"
}

# Function to stop containers
stop_containers() {
    print_status "Stopping containers..."
    docker-compose down 2>/dev/null || true
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    print_success "Containers stopped!"
}

# Function to clean everything
clean_all() {
    print_status "Stopping and removing containers..."
    docker-compose down --rmi all --volumes --remove-orphans 2>/dev/null || true
    docker-compose -f docker-compose.prod.yml down --rmi all --volumes --remove-orphans 2>/dev/null || true
    
    print_status "Removing unused Docker resources..."
    docker system prune -f
    
    print_success "Cleanup completed!"
}

# Function to show logs
show_logs() {
    print_status "Showing logs from running containers..."
    
    # Check if dev containers are running
    if docker-compose ps | grep -q "Up"; then
        print_status "Development containers logs:"
        docker-compose logs -f
    elif docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        print_status "Production container logs:"
        docker-compose -f docker-compose.prod.yml logs -f
    else
        print_warning "No containers are currently running."
        print_status "Start containers first with: $0 dev or $0 prod"
    fi
}

# Main script logic
case "${1:-help}" in
    dev)
        run_dev
        ;;
    prod)
        run_prod
        ;;
    local)
        run_local
        ;;
    test)
        run_tests
        ;;
    stop)
        stop_containers
        ;;
    clean)
        clean_all
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Unknown option: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac 