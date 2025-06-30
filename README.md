# Etsy Seller Automaker

A comprehensive tool for Etsy sellers to automate listing creation, manage shop analytics, and create design mockups.

## Features

- **OAuth Authentication**: Secure Etsy API integration
- **Shop Analytics**: View top sellers and sales data
- **Design Management**: Browse Etsy listings and local design files
- **Mask Creator**: Create masks for mockup images
- **Modern UI**: Beautiful React frontend with Tailwind CSS
- **Comprehensive Testing**: Unit tests for API and utilities

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Docker (for containerized deployment)
- Etsy Developer Account

### Option 1: Docker Deployment (Recommended)

The easiest way to run the application is using Docker:

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd etsy_seller_automater
   ```

2. **Configure environment variables**
   Create a `.env` file in the project root:
   ```env
   CLIENT_ID=your_etsy_client_id
   SHOP_NAME=your_shop_name
   SHOP_URL=https://www.etsy.com/shop/your_shop_name
   LOCAL_ROOT_PATH=/path/to/your/local/files
   ```

3. **Run with Docker**
   
   **Development Mode** (separate frontend and backend containers):
   ```bash
   ./run_docker.sh dev
   ```
   
   **Production Mode** (single container with built frontend):
   ```bash
   ./run_docker.sh prod
   ```

4. **Access the application**
   - Development: Frontend at http://localhost:3000, Backend at http://localhost:3003
   - Production: Application at http://localhost:3003

### Option 2: Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd etsy_seller_automater
   ```

2. **Set up Python environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure environment variables**
   Create a `.env` file in the project root:
   ```env
   CLIENT_ID=your_etsy_client_id
   SHOP_NAME=your_shop_name
   SHOP_URL=https://www.etsy.com/shop/your_shop_name
   LOCAL_ROOT_PATH=/path/to/your/local/files
   ```

5. **Start the servers**
   ```bash
   # Terminal 1: Start backend
   source .venv/bin/activate
   cd server
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 3003
   
   # Terminal 2: Start frontend
   cd frontend
   npm start
   ```

6. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:3003

## Docker Management

The project includes a convenient script for managing Docker containers:

```bash
# Development mode (hot reload, separate containers)
./run_docker.sh dev

# Production mode (optimized, single container)
./run_docker.sh prod

# Run tests
./run_docker.sh test

# Stop all containers
./run_docker.sh stop

# Clean up containers and images
./run_docker.sh clean

# View logs
./run_docker.sh logs

# Show help
./run_docker.sh help
```

### Docker Configuration Files

- `docker-compose.yml` - Development environment with separate frontend/backend
- `docker-compose.prod.yml` - Production environment with built frontend
- `Dockerfile.backend` - Backend service container
- `Dockerfile.frontend` - Frontend service container  
- `Dockerfile.prod` - Production container with multi-stage build

## Testing

The project includes a comprehensive test suite for the backend:

### Running Tests

**With Docker (Recommended):**
```bash
./run_docker.sh test
```

**Locally:**
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
python -m pytest server/tests/ -v
```

### Test Structure

```
server/tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Pytest configuration and fixtures
├── test_api.py              # API route tests
├── test_mask_utils.py       # Mask utility tests
└── test_mask_creator.py     # Mask creator tests
```

### Test Coverage

- **API Routes**: Tests for all major API endpoints
- **Mask Utilities**: Tests for mask validation and saving
- **Integration**: Tests for OAuth flow and data processing

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CLIENT_ID` | Your Etsy API client ID | Yes |
| `SHOP_NAME` | Your Etsy shop name | Yes |
| `SHOP_URL` | Your Etsy shop URL | Yes |
| `LOCAL_ROOT_PATH` | Path to your local design files | Yes |

### OAuth Configuration

The application uses OAuth 2.0 with PKCE for secure authentication. The redirect URI is automatically set to `http://localhost:3000/oauth/redirect` and does not need to be configured in the `.env` file.

## Usage

### Authentication

1. Click "Connect Your Etsy Shop" on the home page
2. Authorize the application in Etsy
3. You'll be redirected back with a success message
4. Your shop data will now be available

### Features

#### Dashboard
- **Overview**: Welcome message and quick stats
- **Analytics**: View top sellers by year with monthly breakdown
- **Designs**: Browse Etsy listings and local PNG files
- **Tools**: Access the mask creator

#### Mask Creator
1. Upload a mockup image
2. Choose drawing mode (point or rectangle)
3. Draw masks on the image
4. Save masks for use in mockup generation

## API Endpoints

### OAuth
- `GET /api/oauth-data` - Get OAuth configuration
- `GET /oauth/redirect` - Handle OAuth token exchange
- `POST /api/oauth-callback` - Alternative OAuth callback

### Shop Data
- `GET /api/user-data` - Get user and shop information
- `GET /api/top-sellers` - Get top selling items
- `GET /api/shop-listings` - Get shop listings with images
- `GET /api/monthly-analytics` - Get monthly sales breakdown

### Local Files
- `GET /api/local-images` - List local PNG files
- `GET /api/local-images/{filename}` - Serve local image file

### Tools
- `POST /api/masks` - Save mask data
- `GET /api/create-gang-sheets` - Create gang sheets

## Development

### Project Structure

```
etsy_seller_automater/
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/           # Page components
│   │   └── index.css        # Tailwind CSS
│   └── package.json
├── server/                  # FastAPI backend
│   ├── api/
│   │   └── routes.py        # API routes
│   ├── engine/              # Business logic
│   ├── tests/               # Test suite
│   │   ├── __init__.py
│   │   ├── conftest.py      # Pytest configuration
│   │   ├── test_api.py      # API tests
│   │   ├── test_mask_utils.py # Utility tests
│   │   └── test_mask_creator.py # Mask creator tests
│   └── main.py              # Server entry point
├── docker-compose.yml       # Development Docker setup
├── docker-compose.prod.yml  # Production Docker setup
├── Dockerfile.backend       # Backend container
├── Dockerfile.frontend      # Frontend container
├── Dockerfile.prod          # Production container
├── run_docker.sh           # Docker management script
├── pytest.ini              # Pytest configuration
├── requirements.txt         # Python dependencies
└── README.md
```

### Building for Production

1. **Build frontend**
   ```bash
   cd frontend
   npm run build
   ```

2. **Start production server**
   ```bash
   source .venv/bin/activate
   python start_server.py
   ```

   Or use Docker:
   ```bash
   ./run_docker.sh prod
   ```

## Troubleshooting

### Common Issues

1. **OAuth Redirect Issues**
   - Ensure your Etsy app is configured with the correct redirect URI
   - The redirect URI should be: `http://localhost:3000/oauth/redirect`

2. **Image Loading Issues**
   - Check that the local images path exists and contains PNG files
   - Verify file permissions

3. **API Connection Issues**
   - Ensure both frontend and backend servers are running
   - Check that the backend is accessible on port 3003

4. **Docker Issues**
   - Make sure Docker is running
   - Check container logs: `./run_docker.sh logs`
   - Clean up and rebuild: `./run_docker.sh clean && ./run_docker.sh dev`

5. **Test Issues**
   - Ensure test dependencies are installed: `pip install pytest pytest-asyncio httpx`
   - Run tests in Docker: `./run_docker.sh test`

### Logs

- Frontend logs: Check browser console or `./run_docker.sh logs`
- Backend logs: Check terminal where uvicorn is running or `./run_docker.sh logs`
- Test logs: Check test output or run with `-v` flag for verbose output

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `./run_docker.sh test`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Check the troubleshooting section
- Review the API documentation
- Open an issue on GitHub 