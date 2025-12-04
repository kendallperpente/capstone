#!/bin/bash
cd /workspaces/capstone

# Remove __pycache__ from git tracking
git rm -r --cached __pycache__

# Add .gitignore
git add .gitignore

# Commit the changes
git commit -m "Add .gitignore and remove __pycache__ from tracking"

# Pull latest changes
git pull origin main --rebase

# Push changes
git push origin main

echo "✓ Git sync complete!"
