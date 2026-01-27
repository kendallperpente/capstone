#!/bin/bash
python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/workspaces/capstone')

# Run the scraper
exec(open('/workspaces/capstone/scrapper.py').read())
PYTHON_EOF
