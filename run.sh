#!/bin/bash
# Move to the script's directory
cd "$(dirname "$0")"

# Execute using the project's virtual environment
exec .venv/bin/python juggle_cursor.py "$@"
