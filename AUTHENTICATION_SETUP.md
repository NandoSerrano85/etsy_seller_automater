# Authentication and Routing Setup

This document describes the authentication and routing system implemented in the Etsy Seller Automater project.

## Overview

The application now uses JWT-based authentication with protected routes. Users must register/login to access the main features of the application.

## Architecture

### Frontend (React)

#### Authentication Context (`frontend/src/contexts/AuthContext.js`)
- Manages user authentication state
- Provides login, register, and logout functions
- Handles JWT token storage in localStorage
- Automatically verifies token validity on app load

#### Protected Routes (`frontend/src/components/ProtectedRoute.js`)
- Wraps components that require authentication
- Redirects unauthenticated users to login page
- Shows loading spinner while verifying authentication

#### API Hook (`frontend/src/hooks/useApi.js`)
- Provides authenticated API calls
- Automatically includes JWT token in request headers
- Handles error responses consistently

### Backend (FastAPI)

#### Authentication Endpoints
- `POST /api/register` - User registration
- `POST /api/login` - User login
- `GET /api/verify-token` - Token verification

#### Protected Endpoints
All sensitive endpoints now require authentication via JWT token:
- `/api/user-data`
- `/api/top-sellers`
- `/api/shop-listings`
- `/api/masks`
- `/api/create-gang-sheets`
- `/api/local-images`
- `/api/monthly-analytics`
- `/api/mockup-images`
- `/api/upload-mockup`
- `/api/orders`

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    root_folder VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    mask_data_path VARCHAR,
    mockup_blank_path VARCHAR,
    watermark_path VARCHAR
);
```

### OAuth Tokens Table
```sql
CREATE TABLE oauth_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, access_token)
);
```

## Usage

### Registration
1. Navigate to `/login`
2. Click "Register" tab
3. Enter email and password
4. Submit form
5. User is automatically logged in and redirected

### Login
1. Navigate to `/login`
2. Enter email and password
3. Submit form
4. User is redirected to the page they were trying to access

### Protected Routes
- `/` (Home) - Requires authentication
- `/mask-creator` - Requires authentication
- `/login` - Public route
- `/welcome` - Public route
- `/oauth/redirect` - Public route

### API Calls
All API calls from the frontend now automatically include the JWT token:

```javascript
import { useApi } from '../hooks/useApi';

const api = useApi();

// GET request with authentication
const data = await api.get('/api/user-data');

// POST request with authentication
const result = await api.post('/api/masks', maskData);
```

## Security Features

1. **Password Hashing**: Passwords are hashed using bcrypt
2. **JWT Tokens**: Secure token-based authentication
3. **Token Expiration**: Tokens expire after 7 days
4. **Protected Routes**: Client-side route protection
5. **API Protection**: Server-side endpoint protection
6. **Automatic Token Verification**: Tokens are verified on app load

## Environment Variables

Make sure these environment variables are set in your `.env` file:

```env
JWT_SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://postgres:postgres@db:5432/etsydb
```

## Testing

To test the authentication system:

1. Start the backend server: `cd server && python main.py`
2. Start the frontend: `cd frontend && npm start`
3. Navigate to `http://localhost:3000`
4. You should be redirected to `/login`
5. Register a new account
6. Test accessing protected routes
7. Test logging out and logging back in

## Future Enhancements

1. **Password Reset**: Add password reset functionality
2. **Email Verification**: Add email verification for new accounts
3. **Remember Me**: Add "remember me" functionality
4. **Session Management**: Add session management for multiple devices
5. **Role-Based Access**: Add different user roles and permissions 