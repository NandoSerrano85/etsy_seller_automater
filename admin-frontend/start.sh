#!/bin/sh
PORT=${PORT:-80}
echo "Starting nginx on port $PORT"
echo "Environment PORT variable: $PORT"

# Create nginx config with the correct port
cat > /etc/nginx/conf.d/default.conf << EOF
server {
    listen $PORT;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Health check endpoint
    location = /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }

    # Handle React Router
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Cache static assets
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}
EOF

echo "Nginx configuration created for port $PORT"
echo "Starting nginx..."
nginx -g "daemon off;"