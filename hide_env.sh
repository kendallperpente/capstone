#!/bin/bash
set -e

cd /workspaces/capstone

echo "🔄 Removing .env from git tracking..."
git rm --cached .env

echo "📝 Adding changes..."
git add .gitignore

echo "💾 Committing..."
git commit -m "Hide .env file with sensitive credentials"

echo "🔄 Pulling latest changes..."
git pull origin main --rebase

echo "📤 Pushing changes..."
git push origin main

echo "✅ All set! .env file is now hidden but still local."
