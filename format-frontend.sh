#!/bin/bash

# Format frontend files with Prettier
echo "🎨 Formatting frontend files with Prettier..."
cd "$(dirname "$0")/frontend"
npm run format
echo "✅ Frontend formatting complete!"