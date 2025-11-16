# Research: AI Image Generation for Name Signs

**Feature**: 001-ai-image-generation
**Date**: 2025-11-16
**Purpose**: Technical research and decision documentation for AI Image Generation component

---

## OpenAI DALL-E 3 API Integration

### Decision: Use OpenAI DALL-E 3 API for POC

**Rationale**:
- Proven text-to-image generation capability with high quality output
- Official Python SDK (`openai` library) with good documentation
- Suitable for name sign generation (handles text-in-image requests well)
- API key authentication simplifies POC setup (no OAuth complexity)
- Pay-per-use pricing model appropriate for POC validation

**Alternatives Considered**:
1. **Stable Diffusion (self-hosted)**: Rejected - requires GPU infrastructure, model management complexity, longer setup time
2. **Midjourney**: Rejected - no official API, Discord-based interaction unsuitable for automation
3. **DALL-E 2**: Rejected - DALL-E 3 offers better quality and text rendering

**Key API Characteristics**:
- **Endpoint**: `POST https://api.openai.com/v1/images/generations`
- **Authentication**: Bearer token (API key in `Authorization` header)
- **Rate Limits**: 50 requests/minute (tier-dependent), 5 concurrent requests
- **Image Sizes**: 1024x1024, 1792x1024, 1024x1792
- **Quality Levels**: `standard` (faster, cheaper) or `hd` (higher detail)
- **Pricing**: ~$0.040-0.080 per image (standard quality)

### Prompt Engineering Best Practices

**Research Findings**:
- DALL-E 3 performs better with descriptive, specific prompts
- Including style descriptors improves aesthetic consistency
- Text rendering improves with explicit "text says..." instructions
- Negative prompts not supported (unlike Stable Diffusion)

**Recommended Prompt Template**:
```
"A [style] name sign design with the text '[user_text]' in a clean, readable font,
suitable for 3D printing. [style_keywords]. Professional product photography,
high contrast, white background."
```

**Style Keywords Mapping**:
- **Modern**: "minimalist, clean lines, sans-serif font, contemporary"
- **Classic**: "elegant, traditional, serif font, timeless"
- **Playful**: "fun, colorful, rounded letters, whimsical"

**Sources**:
- OpenAI DALL-E 3 Documentation: https://platform.openai.com/docs/guides/images
- OpenAI API Reference: https://platform.openai.com/docs/api-reference/images

---

## Python Testing Strategy

### Decision: pytest with pytest-cov, pytest-mock, and respx

**Rationale**:
- **pytest**: Industry standard for Python testing, excellent fixture system, clear assertion syntax
- **pytest-cov**: Integrated coverage reporting, supports 80% minimum requirement
- **pytest-mock**: Simplified mocking based on unittest.mock, cleaner test code
- **respx**: Purpose-built for mocking HTTPX/HTTP requests, ideal for OpenAI API mocking

**Alternatives Considered**:
1. **unittest**: Rejected - more verbose, less feature-rich than pytest
2. **VCR.py**: Considered for recording real API responses - will use for integration tests only
3. **responses library**: Rejected in favor of respx (better HTTPX support)

**Testing Architecture**:

```
tests/
├── unit/              # Fast, isolated, mocked dependencies
│   ├── test_prompt_optimizer.py      # Pure logic, no I/O
│   ├── test_validator.py             # Image validation logic
│   └── test_storage_manager.py       # File path logic (mocked file I/O)
├── integration/       # Component interactions, real/recorded API
│   ├── test_openai_integration.py    # OpenAI API (with VCR.py recordings)
│   └── test_e2e_generation.py        # Full flow (mocked API)
└── contract/          # API contract validation
    └── test_generator_contract.py    # Input/output contract compliance
```

**Mock Strategy**:
- **Unit tests**: Mock all I/O (file system, API calls)
- **Integration tests**: Use VCR.py to record real API responses, replay in tests
- **Contract tests**: Mock API but validate real response structure

**Coverage Configuration**:
```ini
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=html --cov-report=term --cov-fail-under=80"
```

**Sources**:
- pytest Documentation: https://docs.pytest.org/
- pytest-cov: https://pytest-cov.readthedocs.io/
- respx: https://lundberg.github.io/respx/

---

## Image Quality Validation

### Decision: Basic validation with Pillow + file integrity checks

**Rationale**:
- **Pillow (PIL)**: Standard Python imaging library, can verify image properties
- **File integrity**: Verify file exists, is readable, has valid image header
- **Resolution check**: Ensure minimum resolution for 3D printing clarity
- **Format validation**: Confirm PNG/JPEG format

**Quality Criteria** (POC):
1. **File Integrity**: File exists, non-zero size, valid image format
2. **Resolution**: Minimum 1024x1024 pixels (printable quality)
3. **Format**: PNG (preferred) or JPEG
4. **Readability**: Image can be opened and decoded by Pillow

**Alternatives Considered**:
1. **OCR Verification**: Considered using pytesseract to verify text matches prompt - Rejected for POC (adds complexity, OCR accuracy issues)
2. **Aesthetic Scoring**: ML-based quality assessment - Deferred (out of POC scope)
3. **Manual Review**: Human verification - Not feasible for automation

**Validation Implementation**:
```python
def validate_image(image_path: Path) -> ValidationResult:
    """
    Basic quality validation for generated images.

    Checks:
    - File exists and is readable
    - Valid image format (PNG/JPEG)
    - Meets minimum resolution (1024x1024)
    - Image can be decoded
    """
    # Implementation uses Pillow Image.open() and size checks
```

**Future Enhancements** (post-POC):
- OCR verification (pytesseract) to confirm text rendering
- Contrast/clarity analysis
- Printability scoring (assess detail level for 3D extrusion)

**Sources**:
- Pillow Documentation: https://pillow.readthedocs.io/

---

## Error Handling and Retry Strategy

### Decision: Exponential backoff for retryable errors, fast-fail for validation

**Rationale**:
- **Exponential backoff**: Industry standard for API rate limiting
- **Fast-fail**: Input validation errors should not retry (user error)
- **Limited retries**: Maximum 3 attempts prevents infinite loops
- **Error classification**: Different strategies for transient vs permanent errors

**Error Categories and Strategies**:

| Error Type | Strategy | Retry Count | Backoff |
|------------|----------|-------------|---------|
| Rate limit (429) | Exponential backoff | 3 | 2s, 4s, 8s |
| Service error (5xx) | Fixed delay | 3 | 5s, 5s, 5s |
| Authentication (401) | Fail fast | 0 | None |
| Validation error | Fail fast | 0 | None |
| Quality failure | Single retry | 1 | Immediate (modified prompt) |
| Network timeout | Exponential backoff | 3 | 5s, 10s, 20s |

**Exception Hierarchy**:
```python
AIGenerationError (base exception)
├── ValidationError       # Input validation failures (no retry)
├── APIError              # OpenAI API errors
│   ├── AuthenticationError  # Invalid API key (no retry)
│   ├── RateLimitError       # Rate limited (exponential backoff)
│   └── ServiceError         # OpenAI service issue (fixed delay retry)
├── QualityError          # Image quality validation failed (single retry)
└── StorageError          # File I/O errors (no retry)
```

**Implementation Notes**:
- Use `tenacity` library for retry logic (declarative, well-tested)
- Log all retry attempts with context (error type, attempt number)
- Surface original error message to user after max retries

**Alternatives Considered**:
1. **Infinite retries**: Rejected - risk of infinite loops
2. **No retries**: Rejected - transient failures would break automation
3. **Custom retry logic**: Rejected - `tenacity` provides battle-tested implementation

**Sources**:
- tenacity library: https://tenacity.readthedocs.io/
- AWS Retry Best Practices: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/

---

## Configuration Management

### Decision: pydantic-settings for environment-based configuration

**Rationale**:
- **pydantic-settings**: Type-safe configuration with validation
- **Environment variables**: Standard for secrets management (12-factor app)
- **Validation**: Automatic validation of configuration values
- **IDE support**: Type hints enable autocomplete and error detection

**Configuration Structure**:
```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str  # Required, will error if not set

    # Image Generation Defaults
    image_size: str = "1024x1024"
    image_quality: str = "standard"

    # Storage Configuration
    storage_path: Path = Path("./output/generated")

    # Retry Configuration
    max_retries: int = 3
    retry_delay_base: int = 2  # seconds

    # Logging
    log_level: str = "INFO"

    class Config:
        env_prefix = "AI_GEN_"
        env_file = ".env"
        env_file_encoding = "utf-8"
```

**Environment Variables** (`.env` file):
```bash
AI_GEN_OPENAI_API_KEY=sk-...
AI_GEN_IMAGE_SIZE=1024x1024
AI_GEN_IMAGE_QUALITY=standard
AI_GEN_STORAGE_PATH=./output/generated
AI_GEN_LOG_LEVEL=INFO
```

**Alternatives Considered**:
1. **python-decouple**: Simpler but no validation
2. **dynaconf**: Feature-rich but overly complex for POC
3. **ConfigParser**: Manual parsing, no type safety

**Sources**:
- pydantic-settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/

---

## Logging Strategy

### Decision: structlog for structured JSON logging

**Rationale**:
- **Structured logging**: Machine-parseable JSON output
- **Context preservation**: Automatic request ID, timestamps
- **No sensitive data**: Explicit filtering to prevent API key leakage
- **Development UX**: Human-readable console output in development

**Log Levels**:
- **DEBUG**: API request/response details (excluding secrets)
- **INFO**: Generation events (started, completed, file saved)
- **WARNING**: Retry attempts, quality validation failures
- **ERROR**: Unrecoverable errors, max retries exceeded

**Log Format** (JSON in production):
```json
{
  "timestamp": "2025-11-16T12:34:56Z",
  "level": "INFO",
  "event": "image_generated",
  "request_id": "abc123",
  "prompt": "SARAH",
  "style": "modern",
  "generation_time_ms": 2340,
  "image_path": "/output/20251116_abc123_sarah.png"
}
```

**Sensitive Data Filtering**:
- API keys: Masked as `sk-***...***`
- Full prompts: Truncated if >100 chars
- File paths: Relative paths only (no absolute paths with usernames)

**Alternatives Considered**:
1. **Standard logging**: No structured output
2. **loguru**: Simpler but less industry-standard
3. **Python logging**: Too verbose configuration

**Sources**:
- structlog: https://www.structlog.org/

---

## File Storage Organization

### Decision: Timestamp-based organization with content hashing

**Rationale**:
- **Timestamp prefix**: Chronological ordering, easy cleanup
- **Content hash**: Deduplication, uniqueness guarantee
- **Prompt slug**: Human-readable file identification
- **JSON sidecar**: Metadata without modifying image

**File Naming Convention**:
```
{yyyymmdd}_{hhmmss}_{hash}_{prompt_slug}.png
20251116_123456_a1b2c3_welcome_home.png
```

**Directory Structure**:
```
output/generated/
├── 20251116_123456_a1b2c3_sarah.png
├── 20251116_123456_a1b2c3_sarah.json
├── 20251116_123501_d4e5f6_welcome_home.png
└── 20251116_123501_d4e5f6_welcome_home.json
```

**Metadata JSON Example**:
```json
{
  "request_id": "a1b2c3",
  "timestamp": "2025-11-16T12:34:56Z",
  "prompt": "SARAH",
  "optimized_prompt": "A modern name sign design with the text 'SARAH'...",
  "style": "modern",
  "image_path": "20251116_123456_a1b2c3_sarah.png",
  "model": "dall-e-3",
  "size": "1024x1024",
  "quality": "standard",
  "generation_time_ms": 2340,
  "quality_score": 0.95,
  "validation_passed": true
}
```

**Cleanup Policy** (POC):
- Manual cleanup (no automatic deletion)
- Future: Retention policy (e.g., 30 days)

**Alternatives Considered**:
1. **UUID-only naming**: Rejected - not human-readable
2. **Prompt-only naming**: Rejected - collision risk
3. **Database storage**: Out of scope for POC

---

## Dependency Versioning

### Decision: Pin all direct and transitive dependencies

**Rationale**:
- **Reproducibility**: Exact versions ensure consistent behavior
- **Security**: Controlled updates, audit trail
- **Testing**: Same versions in dev/test/prod

**requirements.txt** (production):
```
openai==1.52.0
pydantic==2.9.2
pydantic-settings==2.5.2
pillow==10.4.0
python-dotenv==1.0.1
structlog==24.4.0
tenacity==9.0.0
httpx==0.27.2
```

**requirements-dev.txt** (development):
```
-r requirements.txt
pytest==8.3.3
pytest-cov==5.0.0
pytest-mock==3.14.0
respx==0.21.1
vcrpy==6.0.1
ruff==0.7.0
mypy==1.13.0
```

**Update Strategy**:
- Security patches: Immediate update and test
- Minor versions: Monthly review
- Major versions: Planned migration with testing

**Sources**:
- pip requirements format: https://pip.pypa.io/en/stable/reference/requirements-file-format/

---

## Summary of Key Decisions

| Decision Area | Choice | Rationale |
|---------------|--------|-----------|
| AI Service | OpenAI DALL-E 3 API | Best quality, official SDK, simple auth |
| Testing Framework | pytest + pytest-cov | Industry standard, rich ecosystem |
| API Mocking | respx + VCR.py | HTTPX-compatible, record/replay |
| Image Validation | Pillow + basic checks | Sufficient for POC, extensible |
| Error Handling | tenacity + exponential backoff | Battle-tested, declarative |
| Configuration | pydantic-settings | Type-safe, validated |
| Logging | structlog | Structured, context-aware |
| File Storage | Timestamp + hash naming | Organized, deduplicatable |
| Dependencies | Pinned versions | Reproducible builds |

All decisions align with LeSign Constitution principles (TDD, modular design, Python best practices, local-first POC).
