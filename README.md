# CraftFlow

A comprehensive platform for Etsy sellers to streamline their business with professional mockups, automation tools, and analytics.

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

### 1. **Clone the Repository**

```sh
git clone <repo-url>
cd craftflow
```

### 2. **Environment Setup**

- Copy or create a `.env` file in the project root. For local development, use:
  ```env
  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/etsydb
  JWT_SECRET_KEY=supersecretkey
  ```
- For Docker Compose, the correct `DATABASE_URL` is set automatically.

### 3. **Running the Application**

Use the provided `run_docker.sh` script for all modes:

#### **Development with Docker Compose**

Runs backend, frontend, and database in containers (recommended for most users):

```sh
./run_docker.sh dev
```

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:3003](http://localhost:3003)
- API Docs: [http://localhost:3003/docs](http://localhost:3003/docs)

#### **Production Mode (Docker Compose, single container)**

```sh
./run_docker.sh prod
```

- App: [http://localhost:3003](http://localhost:3003)

#### **Local Backend (no Docker)**

Runs backend using your local Python and connects to your local PostgreSQL:

```sh
./run_docker.sh local
```

- The script will ensure `.env` uses `localhost` for the database host.
- Make sure your local PostgreSQL is running and has a database named `etsydb`.

#### **Other Commands**

- Stop all containers: `./run_docker.sh stop`
- Clean all containers/images/volumes: `./run_docker.sh clean`
- Show logs: `./run_docker.sh logs`
- Run backend tests: `./run_docker.sh test`

## DATABASE_URL Host Explained

| How you run backend  | DATABASE_URL host | How to start backend    |
| -------------------- | ----------------- | ----------------------- |
| Locally (not Docker) | localhost         | `./run_docker.sh local` |
| Docker Compose       | db                | `./run_docker.sh dev`   |

- **Never use `db` as the host for local development.**
- **Never use `localhost` as the host inside Docker Compose.**

## Troubleshooting

### **Database Connection Errors**

- **Error: `could not translate host name "db" to address: Name or service not known`**
  - You are running the backend locally but your `.env` uses `db` as the host. Use `./run_docker.sh local` to fix this automatically.

- **Error: `could not connect to server: Connection refused`**
  - Your local PostgreSQL is not running, or the database/user/password is incorrect.

- **Error: `could not translate host name "localhost" to address` (in Docker Compose)**
  - You are running in Docker Compose but your `.env` uses `localhost`. Use `./run_docker.sh dev` to use the correct host.

### **General Tips**

- Always use the `run_docker.sh` script to avoid host confusion.
- If you switch between local and Docker Compose, the script will update your `.env` as needed.
- For persistent data, Docker Compose uses a named volume for PostgreSQL.

## More Information

- API documentation: [http://localhost:3003/docs](http://localhost:3003/docs)
- For advanced configuration, see `docker-compose.yml` and `.env`.

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

| Variable          | Description                     | Required |
| ----------------- | ------------------------------- | -------- |
| `CLIENT_ID`       | Your Etsy API client ID         | Yes      |
| `SHOP_NAME`       | Your Etsy shop name             | Yes      |
| `SHOP_URL`        | Your Etsy shop URL              | Yes      |
| `LOCAL_ROOT_PATH` | Path to your local design files | Yes      |

### Railway Production Environment Variables

For Railway deployment, configure the following additional variables:

| Variable                | Description               | Required | Example               |
| ----------------------- | ------------------------- | -------- | --------------------- |
| `QNAP_HOST`             | QNAP NAS hostname         | No       | `your-nas.domain.com` |
| `QNAP_USERNAME`         | QNAP NAS username         | No       | `admin`               |
| `QNAP_PASSWORD`         | QNAP NAS password         | No       | `your-password`       |
| `QNAP_PORT`             | QNAP SFTP port (SSH)      | No       | `22` (default)        |
| `SHOPIFY_CLIENT_ID`     | Shopify app client ID     | No       | Your Shopify app ID   |
| `SHOPIFY_CLIENT_SECRET` | Shopify app client secret | No       | Your Shopify secret   |

**QNAP Configuration Notes:**

- The app uses **SFTP** (port 22) for all NAS operations including file uploads, downloads, and mockup image loading
- Only `QNAP_PORT=22` is required for Railway deployment
- Ensure SSH access is enabled and accessible from the internet for Railway deployment
- Path format: `/share/Graphics/ShopName/RelativePath` is used for all file operations
- The SFTP client handles both paramiko-based operations and in-memory file transfers for mockup processing

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
craftflow/
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
