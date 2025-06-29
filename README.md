# Etsy Seller Automaker

A modern web application for Etsy sellers with OAuth authentication and shop management capabilities.

## Features

- 🔐 **OAuth 2.0 Authentication** with Etsy
- ⚛️ **React Frontend** with modern UI/UX
- 🚀 **FastAPI Backend** with high performance
- 🐳 **Docker Support** for easy deployment
- 📱 **Responsive Design** for all devices

## Architecture

```
etsy_seller_automater/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/      # Reusable React components
│   │   ├── pages/          # Page components
│   │   └── App.js          # Main React app
│   ├── public/             # Static assets
│   └── package.json        # Frontend dependencies
├── server/                 # FastAPI backend
│   ├── api/
│   │   └── routes.py       # Main FastAPI application & routes
│   ├── engine/
│   │   └── etsy_oath_token.py  # OAuth utility functions
│   └── main.py             # Server startup script
├── Dockerfile             # Multi-stage Docker build
├── docker-compose.yml     # Docker orchestration
└── requirements.txt       # Python dependencies
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd etsy_seller_automater
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Build the React frontend**
   ```bash
   python build_frontend.py
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   CLIENT_ID=your_etsy_client_id
   CLIENT_SECRET=your_etsy_client_secret
   REDIRECT_URI=http://localhost:3003/oauth/redirect
   SHOP_NAME=your_shop_name
   SHOP_URL=your_shop_url
   ```

5. **Run the application**
   ```bash
   python server/main.py
   ```

6. **Access the application**
   Open your browser and go to `http://localhost:3003`

### Docker Setup

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Or use the startup script**
   ```bash
   python start_server.py --mode docker
   ```

## Development

### Frontend Development

The React frontend is located in the `frontend/` directory:

```bash
cd frontend
npm install
npm start  # Runs on http://localhost:3000
```

### Backend Development

The FastAPI backend is located in the `server/` directory:

```bash
cd server
python main.py  # Runs on http://localhost:3003
```

### API Endpoints

- `GET /api/oauth-data` - Get OAuth configuration
- `GET /api/ping` - Health check endpoint
- `GET /oauth/redirect` - OAuth callback handler
- `GET /api/user-data` - Get user and shop data

## Project Structure

### Frontend (`frontend/`)

- **Components**: Reusable UI components
- **Pages**: Main application pages
- **CSS**: Styled components and global styles
- **Routing**: React Router for navigation

### Backend (`server/`)

- **API Routes** (`server/api/routes.py`): Main FastAPI application with all routes and static file serving
- **OAuth Engine** (`server/engine/etsy_oath_token.py`): Pure OAuth utility functions and token management
- **Main** (`server/main.py`): Server startup and configuration

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CLIENT_ID` | Etsy OAuth client ID | Yes |
| `CLIENT_SECRET` | Etsy OAuth client secret | Yes |
| `REDIRECT_URI` | OAuth redirect URI | Yes |
| `SHOP_NAME` | Your Etsy shop name | No |
| `SHOP_URL` | Your Etsy shop URL | No |
| `HOST` | Server host (default: 127.0.0.1) | No |
| `PORT` | Server port (default: 3003) | No |
| `DEBUG` | Debug mode (default: false) | No |

## Docker Commands

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# Stop containers
docker-compose down

# View logs
docker-compose logs -f

# Rebuild frontend only
docker-compose build --no-cache
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please refer to the [Etsy Developer Documentation](https://developer.etsy.com/documentation/essentials/authentication). 