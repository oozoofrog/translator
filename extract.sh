#!/bin/bash

# Extract EPUB files for translation
# Usage: ./extract.sh <epub_file> [options]

# Exit on error
set -e

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if first argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <epub_file> [options]"
    echo "Options:"
    echo "  --max-chunk-size <size>  Maximum chunk size (default: 3000)"
    echo "  --extract-only           Extract without chunking (raw HTML files only)"
    echo "  --verbose                Enable verbose output"
    exit 1
fi

# Extract the EPUB file
echo "Extracting EPUB: $1"
python3 -m epub_extractor.cli extract "$@"

echo "Extraction complete!"