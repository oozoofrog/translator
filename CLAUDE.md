# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a complete EPUB translation system that converts English novels to Korean EPUB files through automated extraction, translation, and reassembly. The project features a modular architecture with intelligent text segmentation, genre-specific translation prompts, and full EPUB reconstruction capabilities.

**Requirements**: Python 3.6+ (core extractor uses only standard library, making it highly portable)

## Configuration

All default settings are centrally managed in `config.py`:
- Default model: `deepseek-r1:8b` (configurable)
- Default temperature: 0.1
- Default chunk sizes: 1500-3500 characters
- Default genre: fantasy (with auto-detection)
- All scripts automatically use these shared settings

## Development Commands

### Environment Setup
```bash
./activate.sh                      # Auto-install Ollama, setup venv, download models
source venv/bin/activate           # Activate virtual environment manually
pip install -r requirements.txt    # Install dependencies manually
```

### Quick Start (One-Click Translation)
```bash
# Complete English → Korean EPUB translation
./translate_to_korean.sh "english_novel.epub"       # Full automation
./translate_to_korean.sh "novel.epub" --genre sci-fi --verbose
./translate_to_korean.sh "novel.epub" --max-workers 8 --batch-size 10  # Fast parallel mode

# Available genres: fantasy (default), sci-fi, romance, mystery, general
```

### Advanced Workflows

#### Step-by-Step Translation
```bash
# 1. Extract and prepare EPUB for translation
python3 -m epub_extractor.cli extract "novel.epub" --max-chunk-size 3500

# 2. Translate chunks (outputs to translated/ by default)
./translate.sh "novel/"                             # Basic translation
./translate.sh "novel/" --model deepseek-r1:8b      # Different model  
./translate.sh "novel/" --resume                    # Resume interrupted translation

# 3. Build Korean EPUB
./build.sh "novel.epub" "translated/" "novel-ko.epub"
```

#### Translation-Only Workflow
```bash
# If you already have extracted chunks
./translate.sh "extracted_dir/"                     # Output: translated/
./translate.sh "extracted_dir/" "custom_output/"    # Custom output directory
```

#### System Optimization
```bash
# Translation with GPU optimization
./translate.sh "dir/" --num-gpu-layers 35

# Ollama management
ollama serve                       # Start Ollama server
ollama list                        # List installed models
ollama pull llama3-ko:8b           # Download translation model
```

### Using the Modular API
```python
from epub_extractor import EPUBExtractor, OllamaTranslator, build_korean_epub

# Complete workflow programmatically
# 1. Extract EPUB
extractor = EPUBExtractor("novel.epub", max_chunk_size=3000)
extractor.extract("extracted_dir")

# 2. Translate chunks
translator = OllamaTranslator(
    model_name="llama3-ko-simple:8b", 
    genre="fantasy",
    enable_cache=True,      # Translation caching
    num_gpu_layers=None     # Auto GPU layers
)
translator.translate_chunks("extracted_dir", "translated_dir")

# 3. Build Korean EPUB
korean_epub = build_korean_epub("novel.epub", "translated_dir", "novel-ko.epub")
```

### Alternative Entry Points
```bash
# Direct CLI usage
python3 -m epub_extractor.cli extract "novel.epub" --max-chunk-size 3500
python3 -m epub_extractor.cli translate "extracted_dir/"
python3 -m epub_extractor.cli build "novel.epub" "translated/"

# Legacy standalone script (original implementation)
python3 epub_extractor.py "novel.epub" --max-chunk-size 3000
```

## Architecture Overview

### Core Modules (epub_extractor/ package)
- **extractor.py**: Main EPUB extraction engine with metadata handling
- **chunker.py**: Intelligent text segmentation (paragraph → sentence → word priority)
- **parser.py**: HTML-to-text parser preserving paragraph structure (handles `<p>`, `<div>`, `<section>` tags, strips `<script>` and `<style>`)
- **translator.py**: Ollama-based translator with error recovery and progress tracking
- **builder.py**: EPUB reassembly engine that reconstructs translated content into valid EPUB
- **prompts.py**: Genre-specific translation prompts (fantasy, sci-fi, romance, mystery, general)
- **cli.py**: Command-line interface with subcommands (extract/translate/build)
- **utils.py**: Utility functions for chapter name extraction and skip detection

### Complete Translation Pipeline
```
English EPUB → HTML Parsing → Text Extraction → Intelligent Chunking → Ollama Translation → Chunk Reassembly → Korean EPUB
```

### Key Design Patterns
- **Modular separation**: Extraction, parsing, chunking, translation, and building are independent
- **Intelligent chunking**: 3-tier smart splitting (paragraph → sentence → word boundaries)
- **Genre-aware translation**: Different prompts for different novel genres
- **Structure preservation**: Original EPUB structure, metadata, and chapter ordering maintained
- **Progress persistence**: Resumable operations with JSON progress tracking
- **Error resilience**: Automatic retries with exponential backoff
- **One-click automation**: Complete English→Korean EPUB conversion in single command
- **Standards compliance**: Dublin Core metadata standard for EPUB metadata

## File Structure and Data Flow

### Input/Output Structure
```
novel.epub → extracted_dir/
├── info.json              # Book metadata
├── chapters/               # Original chapter files
└── chunks/                 # LLM-optimized chunks
    ├── Chapter_001_part_01.txt
    └── chunk_index.json    # Chunk metadata

translated_dir/
├── translated_chunks/      # Korean translations
├── translation_index.json # Translation statistics
└── translation_progress.json # Resume state

novel-ko.epub              # Final Korean EPUB output
```

### Configuration Files
- **requirements.txt**: `ollama>=0.1.0`, `tqdm>=4.60.0`
- **chunk_index.json**: Chunk ordering and size statistics
- **translation_progress.json**: Completed/failed chunk tracking for resumption

### Root Directory Files
- **epub_extractor.py**: Standalone version of the extractor
- **epub_extractor_modular.py**: Wrapper for modular functionality
- **activate.sh**: Complete environment setup with Ollama installation

## Development Guidelines

### When modifying text processing:
- Test with both small (1000-2000 char) and large (4000-6000 char) chunk sizes
- Ensure paragraph boundaries are preserved when possible
- Validate against sample EPUB files in the repository

### When working with translation:
- Always test Ollama connectivity before making changes (`ollama list`)
- Use appropriate genre prompts for different novel types
- Implement proper error handling for network/model failures
- Test resumption functionality for long translation jobs

### When adding new features:
- Follow the modular pattern: separate concerns into appropriate modules
- Update CLI interface in cli.py with new options (extract/translate/build commands)
- Add corresponding shell script wrappers if needed
- Update translate_to_korean.sh if changes affect the complete workflow
- Ensure new dependencies are added to requirements.txt
- Test with actual EPUB files to ensure structure preservation

## Critical Implementation Details

### Chunk Size Optimization
- Default: 1500-3500 characters (optimized for performance and accuracy)
- Smaller chunks: More accurate translation, potential context loss
- Larger chunks: Better context preservation, slower processing
- Smart splitting: Preserves natural text boundaries (paragraphs > sentences > words)

### System Optimizations
- **Sequential Processing**: Stable, memory-efficient processing with reduced resource usage
- **Translation Caching**: MD5-based caching prevents duplicate translations
- **GPU Layer Optimization**: Automatic or manual GPU memory management
- **Intelligent Progress Tracking**: Real-time progress updates with comprehensive statistics

### Translation Quality Controls
- Low temperature (0.1) for consistency
- Genre-specific prompts prevent content fabrication
- Automatic retry mechanism with exponential backoff
- Progress tracking prevents duplicate work

### Ollama Integration
- Uses ollama-python library for performance (model stays in memory)
- Pre-loads models to reduce first translation latency
- Comprehensive error handling for connection/model issues
- Supports model switching without code changes
- Model detection handles different API response formats

### EPUB Structure Preservation
- Original container.xml and OPF file structure maintained
- Metadata updated with Korean language tags and translator credits
- Chapter ordering and HTML structure completely preserved
- Temporary file management with automatic cleanup
- Support for both EPUB 2.0 and 3.0 formats

### Shell Script Integration
- All scripts use `python3 -m epub_extractor.cli` for consistent module imports
- Virtual environment activation handled automatically
- Script arguments passed through to Python CLI interface
- Error handling and status reporting at shell level

## Known Limitations
- No automated test suite currently exists (testing is manual with sample EPUB files)
- Translation quality depends on Ollama model capabilities
- Large EPUB files may require significant processing time