# LeSign Code Guidelines

**Component**: AI Image Generation
**Python Version**: 3.12
**Last Updated**: 2025-11-16

---

## Overview

This document establishes coding standards, best practices, and development workflows for the LeSign AI Image Generation component and serves as a template for other LeSign components.

**Purpose**:
- Ensure code consistency across the project
- Maintain high code quality and maintainability
- Facilitate onboarding of new developers
- Align with LeSign Constitution principles (TDD, modularity, clear interfaces)

**Quick Reference**: Jump to [Common Commands](#quick-reference) for frequently used operations.

---

## 1. Development Environment Setup

### Python Version Requirement

**Required**: Python 3.12 or higher

**Verify Installation**:
```bash
python3 --version  # Should show Python 3.12.x
```

**Installation** (if needed):
```bash
# macOS (Homebrew)
brew install python@3.12

# Ubuntu/Debian
sudo apt install python3.12

# Or use UV to install Python
uv python install 3.12
```

### Package Manager: UV

**Why UV**: 10-100x faster than pip, integrated environment management, lock file support for reproducibility.

**Installation**:
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

**Verify**:
```bash
uv --version
```

### Project Setup

**Initial Setup** (first time):
```bash
cd backend/ai-generation

# Create virtual environment with Python 3.12
uv venv --python 3.12

# Activate virtual environment (optional, uv run handles this)
source .venv/bin/activate  # macOS/Linux

# Install all dependencies
uv sync

# Verify installation
uv run python --version
uv run pytest --version
```

**Daily Development**:
```bash
# Sync dependencies (after pulling changes)
uv sync

# Run tests
uv run pytest

# Run application
uv run python -m ai_generation.generator
```

### Editor Configuration (VS Code)

**Recommended Extensions**:
- Ruff (charliermarsh.ruff)
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)

**Settings** (.vscode/settings.json):
```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.organizeImports": "explicit"
    }
  },
  "ruff.lint.args": ["--config=pyproject.toml"],
  "python.analysis.typeCheckingMode": "basic",
  "python.testing.pytestEnabled": true
}
```

---

## 2. Code Formatting Standards

### Tool: Ruff Formatter

**Why Ruff**: 10-100x faster than Black, Black-compatible output, written in Rust.

**Configuration** (pyproject.toml):
```toml
[tool.ruff]
target-version = "py312"
line-length = 88  # Black-compatible

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

### Formatting Rules

**Line Length**: 88 characters (Black default)
- Rationale: Balance between readability and space efficiency
- PEP 8 allows up to 99 for code, 79 for docstrings

**Indentation**: 4 spaces (never tabs)
```python
# Good
def my_function():
    if condition:
        do_something()

# Bad
def my_function():
  if condition:  # 2 spaces - WRONG
        do_something()
```

**Quote Style**: Double quotes for strings
```python
# Good
message = "Hello, world!"
name = "Sarah"

# Acceptable (for strings containing double quotes)
message = 'She said "Hello"'

# Bad (inconsistent)
message = 'Hello, world!'  # Single quotes when not needed
```

**Trailing Commas**: Use in multi-line structures
```python
# Good (easier to add/remove items, cleaner diffs)
items = [
    "first",
    "second",
    "third",  # Trailing comma
]

# Acceptable (single line)
items = ["first", "second", "third"]
```

**Blank Lines**:
- 2 blank lines between top-level definitions (classes, functions)
- 1 blank line between method definitions within a class
- 1 blank line to separate logical sections within functions

### Running the Formatter

```bash
# Format all files
ruff format .

# Format specific file
ruff format src/generator.py

# Check formatting without modifying
ruff format --check .

# Format and show diff
ruff format --diff .
```

### Automation

**Pre-commit Hook** (.pre-commit-config.yaml):
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.7.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

**CI/CD Check**:
```bash
# In CI pipeline
ruff format --check .  # Fail if not formatted
```

---

## 3. Linting and Code Quality

### Tool: Ruff Linter

**Why Ruff**: Replaces Flake8, isort, pyupgrade, and more. 10-100x faster.

**Configuration** (pyproject.toml):
```toml
[tool.ruff.lint]
select = [
    "E",     # pycodestyle errors
    "W",     # pycodestyle warnings
    "F",     # Pyflakes
    "UP",    # pyupgrade (Python version-specific improvements)
    "B",     # flake8-bugbear (common bugs)
    "SIM",   # flake8-simplify
    "I",     # isort (import sorting)
    "N",     # pep8-naming
    "S",     # flake8-bandit (security)
    "C90",   # mccabe complexity
]

ignore = [
    "E501",  # Line too long (handled by formatter)
]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]  # Unused imports OK in __init__.py
"tests/**/*" = ["S101"]   # Assert statements OK in tests

[tool.ruff.lint.mccabe]
max-complexity = 10  # Maximum cyclomatic complexity

[tool.ruff.lint.isort]
known-first-party = ["ai_generation"]
```

### Enabled Rule Sets

| Code | Tool | Purpose |
|------|------|---------|
| E, W | pycodestyle | PEP 8 style violations |
| F | Pyflakes | Logical errors, unused imports |
| UP | pyupgrade | Modernize Python syntax for 3.12 |
| B | bugbear | Detect likely bugs |
| SIM | simplify | Suggest simpler code patterns |
| I | isort | Organize imports |
| N | pep8-naming | Naming convention enforcement |
| S | bandit | Security issue detection |
| C90 | mccabe | Complexity checks |

### Running the Linter

```bash
# Lint all files
ruff check .

# Lint with auto-fix
ruff check --fix .

# Lint specific file
ruff check src/generator.py

# Show all errors (no auto-fix)
ruff check . --no-fix

# Watch mode (re-run on file changes)
ruff check . --watch
```

### Common Linting Issues

**Unused Imports (F401)**:
```python
# Bad
import os  # F401: Imported but unused

# Good
import os

def get_path():
    return os.getcwd()
```

**Undefined Name (F821)**:
```python
# Bad
result = undefined_variable  # F821: Undefined name

# Good
result = defined_variable
```

**Complexity (C901)**:
```python
# Bad (too many branches)
def complex_function():  # C901: Too complex (15 > 10)
    if condition1:
        if condition2:
            if condition3:
                # ... many nested conditions

# Good (refactor to reduce complexity)
def simple_function():
    if not is_valid():
        return error()

    process_data()
    return success()
```

---

## 4. Naming Conventions

### Python Naming Standards

**Modules and Packages**: `lowercase_with_underscores`
```python
# Good
ai_generation/
├── generator.py
├── prompt_optimizer.py
└── image_validator.py

# Bad
AIGeneration/
├── Generator.py
├── promptOptimizer.py
```

**Classes**: `PascalCase` (CapitalizedWords)
```python
# Good
class ImageGenerator:
    pass

class OpenAIClient:
    pass

class ValidationError(Exception):
    pass

# Bad
class image_generator:  # Should be PascalCase
    pass

class openAIClient:  # Inconsistent capitalization
    pass
```

**Functions and Variables**: `snake_case`
```python
# Good
def generate_image(prompt: str) -> ImageResult:
    image_path = create_image()
    quality_score = validate(image_path)
    return ImageResult(image_path, quality_score)

# Bad
def GenerateImage(prompt: str):  # Should be snake_case
    ImagePath = create_image()  # Variables should be snake_case
    return imagePath
```

**Constants**: `UPPER_CASE_WITH_UNDERSCORES`
```python
# Good
MAX_RETRIES = 3
API_TIMEOUT_SECONDS = 30
DEFAULT_IMAGE_SIZE = "1024x1024"

# Bad
maxRetries = 3
api_timeout = 30
```

**Private Members**: `_leading_underscore`
```python
# Good
class ImageGenerator:
    def __init__(self):
        self._api_client = OpenAIClient()  # Private attribute

    def generate(self):
        return self._internal_process()  # Private method

    def _internal_process(self):
        # Internal implementation
        pass

# Bad
class ImageGenerator:
    def __init__(self):
        self.api_client = OpenAIClient()  # Looks public
```

**Name Mangling**: `__double_leading_underscore` (rare, for avoiding name conflicts)
```python
class BaseClass:
    def __init__(self):
        self.__private_var = "base"  # Name mangled to _BaseClass__private_var

# Only use when you specifically need to avoid name conflicts in subclasses
```

### Descriptive Names

**Use Intention-Revealing Names**:
```python
# Good
def calculate_generation_time_ms(start: datetime, end: datetime) -> int:
    return int((end - start).total_seconds() * 1000)

# Bad
def calc(s, e):  # Unclear purpose and parameters
    return int((e - s).total_seconds() * 1000)
```

**Avoid Abbreviations** (unless universally understood):
```python
# Good
request_id = generate_uuid()
maximum_retry_count = 3
openai_api_client = OpenAIClient()

# Acceptable (universally understood)
api = OpenAI()
url = "https://example.com"
id = "abc123"

# Bad
req_id = generate_uuid()  # Unclear abbreviation
max_rtry_cnt = 3  # Overly abbreviated
```

**Use Verbs for Functions, Nouns for Variables/Classes**:
```python
# Good
def validate_prompt(prompt: str) -> bool:  # Verb: validate
    return len(prompt) > 0

image_result = generate_image("SARAH")  # Noun: result
validator = ImageValidator()  # Noun: validator

# Bad
def prompt(prompt: str):  # Noun used as verb
    ...

validate = ImageValidator()  # Verb used as noun
```

---

## 5. Type Hints

### Requirement

**All public functions MUST have type hints** for parameters and return values.

**Rationale**: Type hints improve code clarity, enable static analysis, catch bugs early, and improve IDE autocomplete.

### Python 3.12 Type Hint Features

**Native Generic Types** (Python 3.9+):
```python
# Good (Python 3.9+)
def process_items(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}

# Old way (still works but unnecessary)
from typing import List, Dict

def process_items(items: List[str]) -> Dict[str, int]:
    return {item: len(item) for item in items}
```

**Union Types with |** (Python 3.10+):
```python
# Good (Python 3.10+)
def get_result(success: bool) -> str | None:
    return "success" if success else None

# Old way
from typing import Optional

def get_result(success: bool) -> Optional[str]:
    return "success" if success else None
```

**Generic Type Aliases** (Python 3.12+):
```python
# Good (Python 3.12+)
type ImagePath = str
type QualityScore = float
type MetadataDict = dict[str, str | int | float]

def validate(path: ImagePath) -> QualityScore:
    ...

# Old way
from typing import TypeAlias

ImagePath: TypeAlias = str
QualityScore: TypeAlias = float
```

**Type Statement for Generics** (Python 3.12+):
```python
# Good (Python 3.12+)
type Container[T] = list[T] | set[T]

def process[T](items: Container[T]) -> list[T]:
    return list(items)

# Old way (pre-3.12)
from typing import TypeVar, Union

T = TypeVar('T')
Container = Union[list[T], set[T]]
```

### Type Hint Best Practices

**Basic Type Hints**:
```python
def generate_image(
    prompt: str,
    style: str | None = None,
    size: str = "1024x1024"
) -> ImageResult:
    """Generate image with type-safe parameters."""
    ...
```

**Complex Types**:
```python
from pathlib import Path
from datetime import datetime

def save_metadata(
    image_path: Path,
    metadata: dict[str, str | int | float],
    timestamp: datetime
) -> bool:
    """Save metadata to file."""
    ...
```

**Type Aliases for Clarity**:
```python
# Define type aliases for domain concepts
type PromptText = str
type StyleName = str
type RequestID = str

def create_request(
    prompt: PromptText,
    style: StyleName
) -> RequestID:
    ...
```

**Literal Types for Restricted Values**:
```python
from typing import Literal

def generate_image(
    prompt: str,
    style: Literal["modern", "classic", "playful"] | None = None,
    size: Literal["1024x1024", "1792x1024", "1024x1792"] = "1024x1024"
) -> ImageResult:
    """Style and size are restricted to specific values."""
    ...
```

**Callable Types**:
```python
from collections.abc import Callable

def retry_on_failure(
    func: Callable[[str], ImageResult],
    max_retries: int = 3
) -> ImageResult:
    """Retry function on failure."""
    ...
```

### Type Checking

**Tool**: mypy or pyright

**Configuration** (pyproject.toml):
```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true

# Per-module options
[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

**Running Type Checker**:
```bash
# Check all files
mypy src/

# Check specific file
mypy src/generator.py

# Watch mode
mypy src/ --watch
```

---

## 6. Import Organization

### Import Order (PEP 8 + isort)

**Three Sections** (separated by blank lines):

1. **Standard Library** imports
2. **Third-party** imports
3. **Local application** imports

**Example**:
```python
# 1. Standard library imports
import os
import sys
from datetime import datetime
from pathlib import Path

# 2. Third-party imports
import requests
from openai import OpenAI
from pydantic import BaseModel, Field

# 3. Local application imports
from ai_generation.models import ImageRequest, ImageResult
from ai_generation.utils import validate_prompt
from ai_generation.exceptions import ValidationError
```

### Import Formatting

**Absolute vs Relative Imports**:
```python
# Good: Absolute imports (preferred)
from ai_generation.generator import ImageGenerator
from ai_generation.prompt.optimizer import PromptOptimizer

# Acceptable: Relative imports within same package
# (Only use within package structure)
from .generator import ImageGenerator  # Same directory
from ..utils import helper_function  # Parent directory

# Bad: Mixing styles inconsistently
```

**Import Statements**:
```python
# Good: One import per line
import os
import sys

# Good: Multiple items from same module
from typing import Optional, Dict, List

# Good: Multi-line imports (when many items)
from ai_generation.models import (
    ImageRequest,
    ImageResult,
    QualityValidation,
    GenerationMetadata,
)

# Bad: Multiple modules on one line
import os, sys  # Should be separate lines

# Bad: Wildcard imports (avoid)
from module import *  # Unclear what's imported
```

**Sorting**:
```python
# Good: Alphabetically sorted within each group
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Bad: Unsorted
import sys
import json
from pathlib import Path
import os
```

### Ruff isort Configuration

**Automatic Import Sorting**:
```bash
# Ruff automatically sorts imports with the I rules enabled
ruff check --select I --fix .
```

**Configuration** (pyproject.toml):
```toml
[tool.ruff.lint.isort]
known-first-party = ["ai_generation"]
force-single-line = false
lines-after-imports = 2
```

---

## 7. Documentation Standards

### Docstring Style: Google Style

**Why Google Style**: Clean, readable, widely used, well-supported by Sphinx.

**All public functions and classes MUST have docstrings.**

### Function Docstrings

**Template**:
```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """Short one-line summary.

    Longer description explaining what the function does, its purpose,
    and any important details. This can span multiple paragraphs.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter

    Returns:
        Description of return value

    Raises:
        ExceptionType: When and why this exception is raised
        AnotherException: When and why this exception is raised

    Example:
        >>> result = function_name(value1, value2)
        >>> print(result)
        expected_output

    Note:
        Any additional notes or warnings for users.
    """
```

**Real Example**:
```python
def generate_image(
    prompt: str,
    style: str | None = None,
    size: str = "1024x1024"
) -> ImageResult:
    """Generate a name sign image from text prompt.

    Sends a text-to-image generation request to OpenAI's DALL-E 3 API,
    applies prompt optimization based on style preference, and validates
    the resulting image for quality and printability.

    Args:
        prompt: Text to render in the name sign (1-50 characters)
        style: Design aesthetic - "modern", "classic", or "playful".
            Defaults to None (no style optimization).
        size: Image dimensions. Must be one of "1024x1024", "1792x1024",
            or "1024x1792". Defaults to "1024x1024".

    Returns:
        ImageResult containing the generated image path, metadata,
        quality validation results, and generation status.

    Raises:
        ValidationError: If prompt is empty, too long, or contains
            invalid characters (non-Latin).
        AuthenticationError: If OpenAI API key is invalid or missing.
        RateLimitError: If API rate limit exceeded after 3 retry attempts.
        QualityError: If generated image fails quality validation after
            3 retry attempts.
        StorageError: If unable to save image file (disk full, permissions).

    Example:
        >>> generator = ImageGenerator()
        >>> result = generator.generate_image("SARAH", style="modern")
        >>> print(result.image_path)
        output/generated/20251116_123456_abc123_sarah.png
        >>> print(result.metadata.generation_time_ms)
        2340

    Note:
        This function implements automatic retry logic for transient failures
        (rate limits, service errors) with exponential backoff. Storage errors
        fail immediately without retry.
    """
```

### Class Docstrings

```python
class ImageGenerator:
    """Main interface for AI-powered name sign image generation.

    This class provides the primary API for generating name sign images
    from text prompts using OpenAI's DALL-E 3. It handles prompt optimization,
    quality validation, metadata management, and error handling.

    The generator operates locally for POC with sequential request processing.
    Each request generates a unique image file with accompanying metadata.

    Attributes:
        settings: Configuration settings (API key, storage path, etc.)
        api_client: OpenAI API client wrapper
        validator: Image quality validator instance

    Example:
        >>> generator = ImageGenerator()
        >>> result = generator.generate_image("Welcome Home")
        >>> if result.status == "success":
        ...     print(f"Generated: {result.image_path}")
    """

    def __init__(self, settings: Settings | None = None):
        """Initialize the image generator.

        Args:
            settings: Optional Settings object. If None, loads from
                environment variables (.env file).

        Raises:
            ConfigurationError: If required configuration (API key) is missing.
        """
```

### Module Docstrings

```python
"""AI Image Generation - Name Sign Generator.

This module provides the core image generation functionality for the LeSign
platform. It converts text prompts into 2D name sign design images suitable
for 3D printing using OpenAI's DALL-E 3 API.

Main Components:
    - ImageGenerator: Primary API for generating images
    - PromptOptimizer: Enhances prompts for better results
    - ImageValidator: Validates image quality and printability

Example:
    Basic usage for generating a name sign:

    >>> from ai_generation import ImageGenerator
    >>> generator = ImageGenerator()
    >>> result = generator.generate_image("SARAH", style="modern")
    >>> print(result.image_path)
"""
```

### Documentation Tools

**Sphinx Configuration** (docs/conf.py):
```python
extensions = [
    'sphinx.ext.autodoc',      # Auto-generate docs from docstrings
    'sphinx.ext.napoleon',     # Google/NumPy style docstrings
    'sphinx.ext.viewcode',     # Add source code links
    'sphinx.ext.intersphinx',  # Link to other projects
]

napoleon_google_docstring = True
napoleon_numpy_docstring = False
```

**Generate Documentation**:
```bash
# Build HTML docs
cd docs
sphinx-build -b html . _build/html
```

---

## 8. Error Handling

### Exception Hierarchy

**Define Custom Exceptions** for domain-specific errors:

```python
"""Exception hierarchy for AI generation component."""

class AIGenerationError(Exception):
    """Base exception for all AI generation errors."""

    def __init__(self, message: str, details: dict | None = None):
        """Initialize exception with message and optional details.

        Args:
            message: Human-readable error description
            details: Additional context (request_id, etc.)
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(AIGenerationError):
    """Input validation failures (invalid prompt, parameters)."""
    pass


class APIError(AIGenerationError):
    """OpenAI API communication errors."""
    pass


class AuthenticationError(APIError):
    """Invalid or missing API key."""
    pass


class RateLimitError(APIError):
    """API rate limit exceeded."""
    pass


class ServiceError(APIError):
    """OpenAI service unavailable or error."""
    pass


class QualityError(AIGenerationError):
    """Generated image fails quality validation."""
    pass


class StorageError(AIGenerationError):
    """File I/O or storage errors."""
    pass
```

### Error Handling Best Practices

**Catch Specific Exceptions**:
```python
# Good
try:
    result = api_client.generate(prompt)
except requests.HTTPError as e:
    logger.error(f"HTTP error: {e}")
    raise APIError(f"API request failed: {e}") from e
except requests.Timeout as e:
    logger.warning(f"Request timeout: {e}")
    raise ServiceError("API timeout") from e

# Bad: Catching too broad
try:
    result = api_client.generate(prompt)
except Exception:  # Too broad
    raise APIError("Something went wrong")
```

**Preserve Tracebacks with `from`**:
```python
# Good: Chain exceptions with 'from'
try:
    value = int(user_input)
except ValueError as e:
    raise ValidationError(f"Invalid number: {user_input}") from e
# Preserves original traceback

# Bad: Loses traceback
try:
    value = int(user_input)
except ValueError:
    raise ValidationError(f"Invalid number: {user_input}")
# Original error information lost
```

**Use Context Managers for Resources**:
```python
# Good: Context manager ensures cleanup
with open("image.png", "rb") as f:
    data = f.read()
    process(data)
# File automatically closed even if exception occurs

# Good: Custom context manager
from contextlib import contextmanager

@contextmanager
def api_client_connection():
    client = OpenAI()
    try:
        yield client
    finally:
        client.close()

with api_client_connection() as client:
    result = client.generate(prompt)

# Bad: Manual cleanup (error-prone)
f = open("image.png", "rb")
try:
    data = f.read()
    process(data)
finally:
    f.close()  # Easy to forget
```

**EAFP: Easier to Ask for Forgiveness than Permission**:
```python
# Good: EAFP (Pythonic)
try:
    result = data[key]
except KeyError:
    result = default_value

# Less Pythonic: LBYL (Look Before You Leap)
if key in data:
    result = data[key]
else:
    result = default_value
```

### Anti-Patterns to Avoid

**Bare `except` Clauses**:
```python
# Bad: Catches everything including KeyboardInterrupt, SystemExit
try:
    risky_operation()
except:  # NEVER do this
    pass

# Good: Catch specific exceptions
try:
    risky_operation()
except (ValueError, KeyError) as e:
    handle_error(e)
```

**Silent Failures**:
```python
# Bad: Silent failure (no logging, no action)
try:
    save_file(data)
except IOError:
    pass  # Error ignored

# Good: Log and handle appropriately
try:
    save_file(data)
except IOError as e:
    logger.error(f"Failed to save file: {e}")
    raise StorageError("Cannot save image file") from e
```

**Not Re-raising When Appropriate**:
```python
# Bad: Swallows critical error
try:
    critical_operation()
except Exception as e:
    logger.error(f"Error: {e}")
    # Missing: Should re-raise if can't handle

# Good: Re-raise if can't handle
try:
    critical_operation()
except SpecificError as e:
    logger.error(f"Error: {e}")
    cleanup()
    raise  # Re-raise to propagate
```

---

## 9. Testing Guidelines

### Testing Framework

**Required Tools**:
- **pytest**: Test framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Simplified mocking
- **respx**: HTTP request mocking (for OpenAI API)

**Installation**:
```bash
uv add --dev pytest pytest-cov pytest-mock respx
```

### Test Organization

```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Fast, isolated, mocked dependencies
│   ├── test_generator.py
│   ├── test_validator.py
│   ├── test_prompt_optimizer.py
│   └── test_storage_manager.py
├── integration/         # Component interactions
│   ├── test_openai_integration.py
│   └── test_e2e_generation.py
└── contract/            # API contract validation
    └── test_generator_contract.py
```

### Test Best Practices

**Descriptive Test Names**:
```python
# Good: Describes what is being tested and expected outcome
def test_generate_image_with_valid_prompt_returns_success():
    ...

def test_validation_rejects_empty_prompt_with_error():
    ...

def test_retry_logic_attempts_three_times_before_failing():
    ...

# Bad: Unclear what is being tested
def test_generator():
    ...

def test_case_1():
    ...
```

**AAA Pattern** (Arrange-Act-Assert):
```python
def test_prompt_optimization_adds_style_keywords():
    # Arrange: Set up test data and dependencies
    optimizer = PromptOptimizer()
    prompt = "SARAH"
    style = "modern"

    # Act: Execute the code under test
    result = optimizer.optimize(prompt, style)

    # Assert: Verify expected outcomes
    assert "modern" in result.lower()
    assert "minimalist" in result.lower()
    assert "SARAH" in result
```

**Use Fixtures for Common Setup**:
```python
# conftest.py
import pytest
from ai_generation import ImageGenerator, Settings

@pytest.fixture
def test_settings():
    """Test configuration with mock API key."""
    return Settings(
        openai_api_key="test-key-12345",
        storage_path=Path("./test_output"),
        image_size="1024x1024"
    )

@pytest.fixture
def image_generator(test_settings):
    """Configured ImageGenerator instance."""
    return ImageGenerator(test_settings)

# test_generator.py
def test_generator_initialization(image_generator):
    # Use fixture
    assert image_generator is not None
    assert image_generator.settings.image_size == "1024x1024"
```

**Parametrize for Multiple Test Cases**:
```python
import pytest

@pytest.mark.parametrize("prompt,expected_valid", [
    ("SARAH", True),
    ("Welcome Home", True),
    ("", False),           # Empty
    ("A" * 51, False),     # Too long
    ("Hello世界", False),   # Non-Latin
])
def test_prompt_validation(prompt, expected_valid):
    """Test prompt validation with various inputs."""
    is_valid = validate_prompt(prompt)
    assert is_valid == expected_valid
```

### Mocking Best Practices

**Mock External Dependencies**:
```python
def test_api_call_with_mock(mocker):
    """Test OpenAI API call with mocked response."""
    # Mock the external API call
    mock_create = mocker.patch('openai.Image.create')
    mock_create.return_value = {
        "data": [{"url": "https://example.com/image.png"}]
    }

    # Execute function that calls API
    generator = ImageGenerator()
    result = generator.generate_image("TEST")

    # Verify mock was called correctly
    assert mock_create.call_count == 1
    mock_create.assert_called_once_with(
        model="dall-e-3",
        prompt=mocker.ANY,  # Any prompt value
        size="1024x1024"
    )

    # Verify result
    assert result.status == "success"
```

**HTTP Mocking with respx**:
```python
import respx
from httpx import Response

@respx.mock
def test_api_integration():
    """Test API integration with mocked HTTP responses."""
    # Mock HTTP endpoint
    respx.post("https://api.openai.com/v1/images/generations").mock(
        return_value=Response(200, json={
            "data": [{"url": "https://example.com/generated.png"}]
        })
    )

    # Test API call
    generator = ImageGenerator()
    result = generator.generate_image("SARAH")

    assert result.status == "success"
```

### Coverage Requirements

**Minimum**: 80% overall coverage (Constitution requirement)

**Running Coverage**:
```bash
# Run tests with coverage
uv run pytest --cov=src --cov-report=html --cov-report=term

# Open HTML report
open htmlcov/index.html

# Fail if coverage below 80%
uv run pytest --cov=src --cov-fail-under=80
```

**Configuration** (pyproject.toml):
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--cov=src",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
    "-v"
]

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/__init__.py",
    "*/conftest.py"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

---

## 10. Security Best Practices

### Input Validation

**Always Validate and Sanitize Input**:
```python
import re

def validate_prompt(prompt: str) -> str:
    """Validate and sanitize user prompt.

    Raises:
        ValidationError: If prompt is invalid
    """
    # Check length
    if not prompt or len(prompt) > 50:
        raise ValidationError("Prompt must be 1-50 characters")

    # Whitelist allowed characters (Latin alphabet, numbers, spaces)
    if not re.match(r'^[a-zA-Z0-9\s]+$', prompt):
        raise ValidationError("Only Latin characters allowed")

    # Remove leading/trailing whitespace
    return prompt.strip()

# Good: Validate before use
prompt = validate_prompt(user_input)
result = generate_image(prompt)

# Bad: Use input directly
result = generate_image(user_input)  # No validation!
```

### Secrets Management

**Use Environment Variables** (NEVER hardcode):
```python
# Good: Load from environment
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str  # Required, from env

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Load settings
settings = Settings()
api_client = OpenAI(api_key=settings.openai_api_key)

# Bad: Hardcoded secret
api_key = "sk-proj-1234567890abcdef"  # NEVER DO THIS
api_client = OpenAI(api_key=api_key)
```

**.env File** (add to .gitignore):
```bash
# .env
OPENAI_API_KEY=sk-proj-your-actual-key-here
AI_GEN_IMAGE_SIZE=1024x1024
AI_GEN_STORAGE_PATH=./output/generated
```

**.gitignore**:
```
# Never commit secrets
.env
*.env
secrets/
credentials.json
```

### Dependency Security

**Regular Security Audits**:
```bash
# Check for vulnerabilities in dependencies
pip install pip-audit
pip-audit

# Or with UV
uv pip list --format=json | pip-audit --input-format=json

# Update vulnerable packages
uv sync --upgrade
```

**Use Ruff Security Rules**:
```toml
# pyproject.toml
[tool.ruff.lint]
select = ["S"]  # flake8-bandit security checks
```

**Common Security Issues Detected**:
```python
# S301: pickle usage (potential code execution)
import pickle  # Ruff warns: avoid pickle

# S303: insecure MD5/SHA1 usage
import hashlib
hashlib.md5(data)  # Ruff warns: use SHA256+

# S108: hardcoded temp file (predictable path)
open("/tmp/temp.txt", "w")  # Ruff warns

# S608: SQL injection risk
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # Vulnerable
```

### File Operations Security

**Prevent Directory Traversal**:
```python
from pathlib import Path

SAFE_DIR = Path("./output/generated")

def save_file(filename: str, content: bytes):
    """Save file securely within allowed directory.

    Args:
        filename: User-provided filename
        content: File content

    Raises:
        SecurityError: If path escapes safe directory
    """
    # Sanitize filename (remove directory components)
    safe_filename = Path(filename).name

    # Construct full path
    output_path = SAFE_DIR / safe_filename

    # Verify path stays within SAFE_DIR
    if not output_path.resolve().is_relative_to(SAFE_DIR.resolve()):
        raise SecurityError("Invalid file path")

    # Write file
    output_path.write_bytes(content)

# Good: Protected against directory traversal
save_file("image.png", data)  # OK
save_file("../../../etc/passwd", data)  # Raises SecurityError

# Bad: Vulnerable to directory traversal
def save_file_bad(filename: str, content: bytes):
    with open(filename, "wb") as f:  # Accepts any path!
        f.write(content)
```

### Logging Security

**Never Log Sensitive Data**:
```python
import structlog

logger = structlog.get_logger()

# Good: Mask sensitive data
logger.info(
    "api_request",
    api_key=settings.openai_api_key[:7] + "***",  # Masked
    prompt=prompt[:50],  # Truncated
)

# Bad: Logs full API key
logger.info(
    "api_request",
    api_key=settings.openai_api_key,  # EXPOSED!
)
```

---

## 11. Package Management with UV

### Adding Dependencies

**Add Production Dependency**:
```bash
# Add single package
uv add requests

# Add multiple packages
uv add pydantic pillow openai

# Add specific version
uv add "requests==2.31.0"

# Add with version constraint
uv add "pydantic>=2.0,<3.0"
```

**Add Development Dependency**:
```bash
# Add dev dependencies
uv add --dev pytest pytest-cov pytest-mock

# Add linting tools
uv add --dev ruff mypy
```

### Installing Dependencies

```bash
# Install all dependencies from pyproject.toml and uv.lock
uv sync

# Install including dev dependencies (default)
uv sync --all-extras

# Install only production dependencies
uv sync --no-dev

# Update all dependencies
uv sync --upgrade

# Update specific package
uv add --upgrade requests
```

### Lock File (uv.lock)

**Purpose**: Ensures reproducible environments across machines

**Workflow**:
```bash
# Developer adds dependency
uv add some-package
# → Updates pyproject.toml and uv.lock
# → Commit both files

# Other developers/CI pull changes
git pull
uv sync
# → Installs exact versions from uv.lock
```

**Benefits**:
- **Reproducibility**: Same environment everywhere
- **Security**: Hash verification of packages
- **Speed**: Pre-resolved dependencies, no re-resolution
- **Collaboration**: Team gets identical environments

### Running Commands

```bash
# Run Python script
uv run python script.py

# Run module
uv run python -m ai_generation.generator

# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Run with environment variables
uv run --env OPENAI_API_KEY=sk-... python script.py
```

### Common UV Commands

```bash
# Initialize project
uv init

# Create virtual environment
uv venv
uv venv --python 3.12

# Add dependency
uv add package-name
uv add --dev dev-package

# Remove dependency
uv remove package-name

# Update dependencies
uv sync --upgrade
uv add --upgrade package-name

# List installed packages
uv pip list

# Show dependency tree
uv pip tree

# Lock dependencies without installing
uv lock

# Clean cache
uv clean
```

---

## 12. Development Workflow

### Daily Development Cycle

**1. Start of Day**:
```bash
# Pull latest changes
git pull

# Sync dependencies (if pyproject.toml or uv.lock changed)
uv sync

# Verify environment
uv run python --version
uv run pytest --version
```

**2. Test-Driven Development (TDD)**:
```bash
# 1. Write test first
# Create tests/unit/test_new_feature.py

# 2. Verify test fails (Red)
uv run pytest tests/unit/test_new_feature.py
# → Test should fail (feature not implemented yet)

# 3. Implement feature
# Write code in src/

# 4. Verify test passes (Green)
uv run pytest tests/unit/test_new_feature.py
# → Test should pass

# 5. Refactor if needed
# Improve code quality while keeping tests green

# 6. Run all tests
uv run pytest
```

**3. Code Quality Checks**:
```bash
# Fix linting issues
ruff check --fix .

# Format code
ruff format .

# Type check
mypy src/

# Run tests with coverage
uv run pytest --cov=src --cov-report=term
```

**4. Commit Changes**:
```bash
# Stage files
git add .

# Commit with descriptive message
git commit -m "feat: add prompt optimization for modern style

- Implement PromptOptimizer class
- Add style-specific keyword mapping
- Add tests for prompt enhancement
- Update documentation"

# Push changes
git push
```

### Pre-commit Hooks

**Installation** (.pre-commit-config.yaml):
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.7.0
    hooks:
      # Run linter with auto-fix
      - id: ruff
        args: [--fix]
      # Run formatter
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic]
```

**Setup Pre-commit**:
```bash
# Install pre-commit
uv add --dev pre-commit

# Install hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

### CI/CD Pipeline Checks

**GitHub Actions** (.github/workflows/ci.yml):
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install UV
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Setup Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync

      - name: Lint
        run: ruff check .

      - name: Format check
        run: ruff format --check .

      - name: Type check
        run: mypy src/

      - name: Run tests
        run: uv run pytest --cov=src --cov-fail-under=80

      - name: Security check
        run: pip-audit
```

---

## 13. Python 3.12 Specific Features

### Leverage New Features

**Improved F-Strings** (PEP 701):
```python
# Python 3.12: More flexible f-string parsing
def format_message(name: str, items: list[str]) -> str:
    # Can now nest quotes more naturally
    return f"Hello {name}, you have {len(items)} items: {', '.join(f'"{item}"' for item in items)}"

# Can use backslashes in f-string expressions
path = f"C:\\Users\\{username}\\Documents"
```

**Generic Type Syntax** (PEP 695):
```python
# Old way (pre-3.12)
from typing import TypeVar, Generic

T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self, value: T):
        self.value = value

# New way (Python 3.12+)
class Container[T]:
    def __init__(self, value: T):
        self.value = value

# Type aliases
type Point = tuple[float, float]
type Vector[T] = list[T]
```

**@override Decorator** (PEP 698):
```python
from typing import override

class BaseGenerator:
    def generate(self, prompt: str) -> str:
        return "base"

class ImageGenerator(BaseGenerator):
    @override  # Validates that this actually overrides parent method
    def generate(self, prompt: str) -> str:
        return "image"

    @override
    def generete(self, prompt: str) -> str:  # Typo!
        # TypeError: Method 'generete' does not override any method
        pass
```

**Performance Improvements**:
```python
# Comprehensions are faster in 3.12
# Use comprehensions where appropriate
squares = [x**2 for x in range(1000)]  # Up to 2x faster

# isinstance() checks are faster
if isinstance(protocol_obj, RuntimeCheckableProtocol):  # 2-20x faster
    ...
```

### Migration from Python 3.11

**Removed Modules**:
```python
# No longer available in 3.12
import distutils  # Removed - use setuptools or build
import smtpd      # Removed - use aiosmtpd

# Update code to use alternatives
```

**Deprecated Features**:
```python
# These will be removed in future versions
import asyncore  # Use asyncio
import imp       # Use importlib
```

---

## 14. Project-Specific Guidelines

### Alignment with LeSign Constitution

**I. Modular Components**:
- Keep components self-contained
- Define clear input/output contracts
- Enable independent testing
- Document component boundaries

**II. Test-Driven Development**:
- Write tests BEFORE implementation
- Maintain 80%+ coverage (enforced in CI)
- Follow Red-Green-Refactor cycle
- All public APIs must have tests

**III. Clear Interfaces & Contracts**:
- Document all contracts explicitly
- Use type hints for all public APIs
- Maintain API contract documentation
- Version contracts when changing interfaces

**IV. Local-First POC**:
- Local execution (no cloud for POC)
- Minimal dependencies
- Simple, direct solutions
- Clear migration path to production

**V. Python & Best Practices**:
- Environment variables for secrets
- Structured logging (JSON format)
- Pinned dependency versions
- Clear code organization

### Component Structure

**Follow Standard Layout**:
```
backend/ai-generation/
├── src/
│   ├── __init__.py
│   ├── generator.py        # Main public API
│   ├── api/                # OpenAI client
│   ├── prompt/             # Prompt optimization
│   ├── validation/         # Quality validation
│   └── storage/            # File management
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── config/
│   └── settings.py
├── CODE_GUIDELINES.md      # This file
├── pyproject.toml          # Configuration
└── README.md               # Component docs
```

### Configuration Pattern

**Use pydantic-settings**:
```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Required settings
    openai_api_key: str

    # Optional settings with defaults
    image_size: str = "1024x1024"
    storage_path: Path = Path("./output/generated")
    log_level: str = "INFO"

    class Config:
        env_prefix = "AI_GEN_"
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### Structured Logging

**Use structlog** for JSON logging:
```python
import structlog

logger = structlog.get_logger()

# Log with structured data
logger.info(
    "image_generated",
    request_id=request_id,
    prompt=prompt[:50],  # Truncate long values
    generation_time_ms=duration,
    image_path=str(image_path),
)

# Never log sensitive data
logger.info(
    "api_call",
    api_key=api_key[:7] + "***",  # Mask secrets
)
```

### File Storage Conventions

**Naming Pattern**:
```
{yyyymmdd}_{hhmmss}_{request_id}_{prompt_slug}.png
20251116_123456_abc123de_welcome_home.png
```

**Metadata Sidecar**:
```
{yyyymmdd}_{hhmmss}_{request_id}_{prompt_slug}.json
20251116_123456_abc123de_welcome_home.json
```

---

## 15. Quick Reference

### Common Commands

**Project Setup**:
```bash
# Initial setup
cd backend/ai-generation
uv venv --python 3.12
uv sync

# After pulling changes
uv sync
```

**Development**:
```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src --cov-report=html

# Lint code
ruff check .

# Lint with auto-fix
ruff check --fix .

# Format code
ruff format .

# Type check
mypy src/

# Run application
uv run python -m ai_generation
```

**Dependency Management**:
```bash
# Add dependency
uv add package-name

# Add dev dependency
uv add --dev package-name

# Update dependencies
uv sync --upgrade

# Remove dependency
uv remove package-name
```

**Pre-commit**:
```bash
# Install hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

### File Locations

**Configuration**:
- `pyproject.toml` - Ruff, pytest, mypy, project metadata
- `.env` - Environment variables (secrets)
- `.ruff.toml` - Alternative Ruff config location

**Code**:
- `src/` - Source code
- `tests/` - Test code
- `config/` - Configuration modules

**Documentation**:
- `CODE_GUIDELINES.md` - This file
- `README.md` - Component documentation
- `docs/` - Sphinx documentation

### Help Resources

**Official Documentation**:
- Python 3.12: https://docs.python.org/3.12/
- PEP 8: https://peps.python.org/pep-0008/
- Ruff: https://docs.astral.sh/ruff/
- UV: https://docs.astral.sh/uv/
- pytest: https://docs.pytest.org/
- mypy: https://mypy.readthedocs.io/
- pydantic: https://docs.pydantic.dev/

**LeSign Documentation**:
- Constitution: `../../.specify/memory/constitution.md`
- Project Overview: `../../OVERVIEW.md`
- Implementation Plan: `../../PLAN.md`
- Spec: `../../specs/001-ai-image-generation/spec.md`

**Community**:
- Python Discord: https://discord.gg/python
- Stack Overflow: https://stackoverflow.com/questions/tagged/python-3.12

---

## 16. Checklist for Code Reviews

Use this checklist when reviewing code:

### Code Quality
- [ ] Code follows PEP 8 (enforced by Ruff)
- [ ] All public functions have type hints
- [ ] All public functions have docstrings (Google style)
- [ ] No hardcoded secrets or credentials
- [ ] No overly complex functions (McCabe complexity <10)

### Testing
- [ ] New code has tests (unit/integration as appropriate)
- [ ] Tests follow AAA pattern (Arrange-Act-Assert)
- [ ] Test coverage meets 80% minimum
- [ ] Tests have descriptive names
- [ ] External dependencies are mocked

### Security
- [ ] Input is validated and sanitized
- [ ] No SQL injection vulnerabilities
- [ ] File paths are validated (no directory traversal)
- [ ] Sensitive data is not logged
- [ ] Dependencies have no known vulnerabilities

### Documentation
- [ ] README updated if public API changed
- [ ] Docstrings updated if function signature changed
- [ ] API contracts documented if interfaces changed
- [ ] Comments explain "why" not "what"

### Architecture
- [ ] Follows modular component principles
- [ ] Clear separation of concerns
- [ ] Minimal dependencies between modules
- [ ] Error handling is appropriate
- [ ] Aligns with LeSign Constitution

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-16 | Initial code guidelines for AI Image Generation component |

---

**Questions or Suggestions?**

If you have questions about these guidelines or suggestions for improvements, please open an issue or discuss with the team.
