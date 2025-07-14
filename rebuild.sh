#!/bin/bash

# Rebuild EPUB from extracted HTML files
# Usage: ./rebuild.sh <original_epub> <extracted_dir> [output_epub]

# Exit on error
set -e

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if required arguments are provided
if [ $# -lt 2 ]; then
    echo "Usage: $0 <original_epub> <extracted_dir> [output_epub]"
    echo "Example: $0 novel.epub extracted/ novel-rebuilt.epub"
    echo ""
    echo "This script rebuilds an EPUB file from extracted HTML files."
    echo "Useful for cases where you manually edited the extracted HTML files."
    exit 1
fi

ORIGINAL_EPUB="$1"
EXTRACTED_DIR="$2"
OUTPUT_EPUB="${3:-}"

# If output file not specified, create default name
if [ -z "$OUTPUT_EPUB" ]; then
    BASE_NAME=$(basename "$ORIGINAL_EPUB" .epub)
    OUTPUT_EPUB="${BASE_NAME}-rebuilt.epub"
fi

# Check if original EPUB exists
if [ ! -f "$ORIGINAL_EPUB" ]; then
    echo "Error: Original EPUB file not found: $ORIGINAL_EPUB"
    exit 1
fi

# Check if extracted directory exists
if [ ! -d "$EXTRACTED_DIR" ]; then
    echo "Error: Extracted directory not found: $EXTRACTED_DIR"
    exit 1
fi

# Check if chapters directory exists
if [ ! -d "$EXTRACTED_DIR/chapters" ]; then
    echo "Error: No chapters directory found in: $EXTRACTED_DIR"
    echo "Make sure you extracted the EPUB with --extract-only option"
    exit 1
fi

echo "🔧 Rebuilding EPUB"
echo "Original: $ORIGINAL_EPUB"
echo "Extracted: $EXTRACTED_DIR"
echo "Output: $OUTPUT_EPUB"

# Use the rebuild command to rebuild EPUB
python3 -m epub_extractor.cli rebuild "$ORIGINAL_EPUB" "$EXTRACTED_DIR" --output "$OUTPUT_EPUB"

echo "✅ EPUB rebuilt successfully: $OUTPUT_EPUB"