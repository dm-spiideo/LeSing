# Quickstart: AI Image Generation

**Feature**: 001-ai-image-generation
**Date**: 2025-11-16
**Audience**: Developers implementing or using the AI Image Generation component

---

## Prerequisites

- Python 3.11 or higher
- OpenAI API key (sign up at https://platform.openai.com/)
- pip or pip virtual environment
- macOS or Linux (POC target platforms)

---

## Quick Setup (5 minutes)

### 1. Clone and Navigate

```bash
cd /path/to/lesign
cd backend/ai-generation
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development/testing
```

### 4. Configure Environment

Create `.env` file in `backend/ai-generation/`:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```bash
AI_GEN_OPENAI_API_KEY=sk-proj-YOUR_API_KEY_HERE
AI_GEN_IMAGE_SIZE=1024x1024
AI_GEN_IMAGE_QUALITY=standard
AI_GEN_STORAGE_PATH=./output/generated
AI_GEN_LOG_LEVEL=INFO
```

### 5. Verify Setup

```bash
pytest tests/ -v
```

If tests pass, you're ready to generate images!

---

## Basic Usage

### Generate Your First Image

```python
from ai_generation import AIImageGenerator

# Initialize generator (loads config from .env)
generator = AIImageGenerator()

# Generate a simple name sign
result = generator.generate_image("SARAH")

if result.status == "success":
    print(f"✅ Image generated: {result.image_path}")
    print(f"⏱️  Time: {result.metadata.generation_time_ms}ms")
    print(f"📊 Quality score: {result.metadata.quality_validation.quality_score}")
else:
    print(f"❌ Generation failed: {result.error}")
```

**Expected Output**:
```
✅ Image generated: output/generated/20251116_123456_abc123_sarah.png
⏱️  Time: 2340ms
📊 Quality score: 1.0
```

### Generate with Style

```python
# Modern style
result = generator.generate_image("Welcome Home", style="modern")

# Classic style
result = generator.generate_image("The Smiths", style="classic")

# Playful style
result = generator.generate_image("Party Time", style="playful")
```

### Custom Size and Quality

```python
# High definition, wide format
result = generator.generate_image(
    prompt="CELEBRATION",
    style="playful",
    size="1792x1024",  # Wider format
    quality="hd"       # High definition (more expensive)
)
```

---

## Common Workflows

### Workflow 1: Basic Generation Pipeline

```python
from ai_generation import AIImageGenerator
from pathlib import Path

def generate_name_sign(text: str, style: str = None):
    """Generate a name sign image and return path."""
    generator = AIImageGenerator()

    try:
        result = generator.generate_image(text, style=style)

        if result.status == "success":
            print(f"Generated: {result.image_path}")
            return result.image_path
        else:
            print(f"Failed: {result.error}")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None

# Usage
image_path = generate_name_sign("DANIEL", style="modern")
```

### Workflow 2: Batch Generation

```python
prompts = ["SARAH", "DANIEL", "Welcome Home", "The Smiths"]
generator = AIImageGenerator()

for prompt in prompts:
    try:
        result = generator.generate_image(prompt, style="modern")
        if result.status == "success":
            print(f"✅ {prompt}: {result.image_path}")
        else:
            print(f"❌ {prompt}: {result.error}")
    except Exception as e:
        print(f"❌ {prompt}: {e}")
```

### Workflow 3: Validate Existing Image

```python
from pathlib import Path

generator = AIImageGenerator()

# Validate previously generated image
image_path = Path("output/generated/20251116_123456_abc123_sarah.png")
validation = generator.validate_image(image_path)

if validation.validation_passed:
    print(f"✅ Image valid: {validation.width}x{validation.height}")
else:
    print(f"❌ Validation failed (score: {validation.quality_score})")
    if not validation.file_exists:
        print("   - File does not exist")
    if not validation.format_valid:
        print("   - Invalid format")
    if not validation.resolution_met:
        print(f"   - Resolution too low: {validation.width}x{validation.height}")
```

---

## Error Handling

### Handle Common Errors

```python
from ai_generation import AIImageGenerator
from ai_generation.exceptions import (
    ValidationError,
    RateLimitError,
    AuthenticationError,
    QualityError
)

generator = AIImageGenerator()

try:
    result = generator.generate_image("SARAH")

except ValidationError as e:
    print(f"Invalid input: {e.message}")
    # Fix: Check prompt is 1-50 characters, valid style/size/quality

except AuthenticationError as e:
    print(f"API key invalid: {e.message}")
    # Fix: Check AI_GEN_OPENAI_API_KEY in .env

except RateLimitError as e:
    print(f"Rate limited: {e.message}")
    # Fix: Wait 60 seconds and retry

except QualityError as e:
    print(f"Quality check failed: {e.message}")
    # Fix: Try different prompt or style

except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Development Workflows

### Run Tests

```bash
# All tests
pytest

# Unit tests only (fast)
pytest tests/unit/

# Integration tests (requires API key)
pytest tests/integration/

# With coverage report
pytest --cov=src --cov-report=html
```

### Lint and Format

```bash
# Check code quality
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Type checking
mypy src/
```

### Add New Test

```python
# tests/unit/test_prompt_optimizer.py
from ai_generation.prompt import PromptOptimizer

def test_modern_style_adds_keywords():
    """Test that modern style adds appropriate keywords."""
    optimizer = PromptOptimizer()
    result = optimizer.optimize("SARAH", style="modern")

    assert "modern" in result.lower()
    assert "minimalist" in result.lower() or "clean" in result.lower()
    assert "SARAH" in result
```

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

generator = AIImageGenerator()
result = generator.generate_image("TEST")  # Verbose output
```

---

## Integration with 3D Model Pipeline

### File Handoff

AI Generation writes files to `output/generated/`:

```
output/generated/
├── 20251116_123456_abc123_sarah.png      # Image file
└── 20251116_123456_abc123_sarah.json     # Metadata
```

### Read Metadata in 3D Pipeline

```python
import json
from pathlib import Path

# 3D Pipeline code
def process_generated_image(image_path: Path):
    """Process AI-generated image for 3D conversion."""

    # Load metadata
    metadata_path = image_path.with_suffix('.json')
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    # Extract information
    prompt = metadata['request']['prompt']
    quality_score = metadata['quality_validation']['quality_score']

    print(f"Processing '{prompt}' (quality: {quality_score})")

    # Proceed with 3D conversion...
```

---

## Troubleshooting

### Issue: "No module named 'ai_generation'"

**Solution**: Activate virtual environment and install dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "AuthenticationError: Invalid API key"

**Solution**: Check `.env` file has correct `AI_GEN_OPENAI_API_KEY`
```bash
cat .env | grep AI_GEN_OPENAI_API_KEY
# Should show: AI_GEN_OPENAI_API_KEY=sk-proj-...
```

### Issue: "RateLimitError: Rate limit exceeded"

**Solution**: OpenAI API has rate limits. Wait 60 seconds or reduce request frequency.

### Issue: "QualityError: Generated image failed validation"

**Solution**: Try different prompt or style. Check generated image manually to understand issue.

### Issue: Tests fail with "No API key found"

**Solution**: Set API key environment variable for tests:
```bash
export AI_GEN_OPENAI_API_KEY=sk-proj-...
pytest
```

Or use `.env` file (pytest-dotenv plugin loads it automatically).

---

## Performance Tips

### Optimize for Speed

1. **Use standard quality** (default) instead of HD
2. **Use 1024x1024 size** (default) for faster generation
3. **Enable caching** in development (VCR.py for repeated API calls)

### Monitor Costs

```python
# Each generation costs approximately:
# - Standard quality: $0.040 per image
# - HD quality: $0.080 per image

# Track costs
generation_count = 0
def generate_with_tracking(prompt):
    global generation_count
    result = generator.generate_image(prompt)
    if result.status == "success":
        generation_count += 1
        estimated_cost = generation_count * 0.040
        print(f"💰 Estimated cost: ${estimated_cost:.2f}")
    return result
```

---

## Next Steps

1. **Implement**: Use `AIImageGenerator` in your code
2. **Test**: Write tests for your integration
3. **Monitor**: Check logs and quality scores
4. **Iterate**: Refine prompts based on output quality

**Read More**:
- [API Contract](contracts/api-contract.md) - Full API reference
- [Data Model](data-model.md) - Entity definitions
- [Research](research.md) - Technical decisions and rationale

---

## Example: Complete Integration

```python
#!/usr/bin/env python3
"""
Complete example: Generate name signs for a list of names.
"""

from ai_generation import AIImageGenerator
from ai_generation.exceptions import AIGenerationError
from pathlib import Path
import json

def main():
    # Initialize
    generator = AIImageGenerator()
    names = ["SARAH", "DANIEL", "The Smiths", "Welcome Home"]

    print("LeSign AI Image Generation Demo")
    print("=" * 40)

    # Generate images
    results = []
    for i, name in enumerate(names, 1):
        print(f"\n[{i}/{len(names)}] Generating '{name}'...")

        try:
            result = generator.generate_image(name, style="modern")

            if result.status == "success":
                print(f"  ✅ Success: {result.image_path}")
                print(f"  ⏱️  Time: {result.metadata.generation_time_ms}ms")
                print(f"  📊 Quality: {result.metadata.quality_validation.quality_score}")
                results.append(result)
            else:
                print(f"  ❌ Failed: {result.error}")

        except AIGenerationError as e:
            print(f"  ❌ Error: {e}")

    # Summary
    print("\n" + "=" * 40)
    print(f"Generated {len(results)}/{len(names)} images successfully")

    if results:
        avg_time = sum(r.metadata.generation_time_ms for r in results) / len(results)
        print(f"Average generation time: {avg_time:.0f}ms")

if __name__ == "__main__":
    main()
```

**Run it**:
```bash
python example_integration.py
```

**Expected Output**:
```
LeSign AI Image Generation Demo
========================================

[1/4] Generating 'SARAH'...
  ✅ Success: output/generated/20251116_123456_abc123_sarah.png
  ⏱️  Time: 2340ms
  📊 Quality: 1.0

[2/4] Generating 'DANIEL'...
  ✅ Success: output/generated/20251116_123501_def456_daniel.png
  ⏱️  Time: 2280ms
  📊 Quality: 1.0

...

========================================
Generated 4/4 images successfully
Average generation time: 2350ms
```

---

**🎉 You're ready to generate AI-powered name sign images!**
