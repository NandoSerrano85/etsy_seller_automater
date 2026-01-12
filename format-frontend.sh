#!/bin/bash

# Format admin frontend files with Prettier
echo "🎨 Formatting admin frontend files with Prettier..."
cd "$(dirname "$0")/admin-frontend"
npm run format
echo "✅ Admin frontend formatting complete!"