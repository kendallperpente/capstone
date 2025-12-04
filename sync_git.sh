#!/bin/bash
set -e

cd /workspaces/capstone

echo "🔄 Fetching latest changes..."
git fetch origin

echo "🔄 Pulling changes with rebase..."
git pull origin main --rebase

echo "✅ Pull successful!"
echo "📤 Pushing your changes..."
git push origin main

echo "✅ Push successful! Your changes are now synced."
