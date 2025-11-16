# AI Image Generation Examples

This directory contains example scripts demonstrating how to use the AI Image Generator.

## Prerequisites

1. Install dependencies:
   ```bash
   pip install -e .
   ```

2. Set up your OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

## Examples

### Basic Usage (`basic_usage.py`)

The simplest way to generate a name sign image:

```bash
python examples/basic_usage.py
```

This example shows:
- Initializing the generator
- Generating a basic image
- Checking the result status
- Accessing metadata

### Styled Generation (`styled_usage.py`)

Generate images with different design styles:

```bash
python examples/styled_usage.py
```

This example demonstrates:
- Using the `modern`, `classic`, and `playful` styles
- How styles affect the optimized prompt
- Generating without a style

### Image Validation (`validation_usage.py`)

Validate image quality for 3D printing:

```bash
python examples/validation_usage.py
```

This example shows:
- Validating image resolution and format
- Interpreting quality scores
- Checking 3D printing suitability

## Configuration

All examples use environment variables for configuration. You can customize:

- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `STORAGE_PATH` - Where to save images (default: `./output`)
- `IMAGE_SIZE` - Image dimensions (default: `1024x1024`)
- `IMAGE_QUALITY` - Quality level (default: `standard`)
- `MAX_RETRIES` - Maximum retry attempts (default: `3`)
- `LOG_LEVEL` - Logging verbosity (default: `INFO`)

See `config/settings.py` for all available settings.
