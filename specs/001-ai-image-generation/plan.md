# Implementation Plan: AI Image Generation for Name Signs

**Branch**: `001-ai-image-generation` | **Date**: 2025-11-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-ai-image-generation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

AI-powered text-to-image generation component that converts user text prompts (e.g., "SARAH", "Welcome Home") into 2D name sign design images suitable for 3D printing. This is the first stage of the LeSign POC pipeline, using OpenAI's DALL-E 3 API for image generation with local file storage and quality validation to ensure reliability in the automated manufacturing workflow.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: openai (DALL-E 3 API client), pydantic (data validation), pillow (image processing), pytest (testing), ruff (linting)
**Storage**: Local file system (PNG/JPEG images + JSON metadata files)
**Testing**: pytest with pytest-cov (coverage), pytest-mock (mocking), respx (HTTP mocking for API tests)
**Target Platform**: Local development environment (macOS/Linux), POC only - no cloud deployment
**Project Type**: Single library/component (backend processing component)
**Performance Goals**: <30 seconds image generation (90th percentile), <10 seconds unit test execution
**Constraints**: Local execution only, 80% minimum test coverage, API key authentication, sequential processing
**Scale/Scope**: POC - single component, sequential request processing, 50-character prompt limit, English/Latin text focus

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Modular Components ✅ PASS

- **Self-contained**: Component operates independently with no external dependencies except OpenAI API
- **Independently testable**: All functionality can be tested in isolation with mocked API calls
- **Well-documented**: Comprehensive documentation planned (README, API docs, contracts)
- **Composable**: Clear input (text prompt) and output (image file + metadata) for pipeline integration

**Status**: Compliant - component boundaries clearly defined

### II. Test-Driven Development ✅ PASS

- **Tests first**: TDD workflow explicitly planned with Red-Green-Refactor cycle
- **Fail before implement**: Process requires test failure verification before implementation
- **80% coverage**: Minimum 80% coverage mandated, target 90%+
- **Public API tests**: All public methods will have comprehensive test coverage

**Status**: Compliant - TDD is core methodology, test framework and strategy documented

### III. Clear Interfaces & Contracts ✅ PASS

- **Input contract**: Defined (prompt: str, style: optional str, size: optional str)
- **Output contract**: Defined (image_path, metadata, status, error handling)
- **API boundaries**: Public API interface specified (generate_image, validate_image)
- **Error handling**: Exception hierarchy defined (ValidationError, APIError, QualityError, StorageError)

**Status**: Compliant - contracts will be fully documented in Phase 1

### IV. Local-First POC ✅ PASS

- **Local execution**: Component runs entirely locally with no cloud deployment
- **Minimal dependencies**: Uses OpenAI API (external), local file storage, standard Python libraries
- **Simple solutions**: Direct file-based handoff to 3D pipeline, no message queues or complex orchestration
- **Architectural focus**: Establishes clear boundaries for future cloud migration

**Status**: Compliant - POC scoped appropriately for local execution

### V. Python & Best Practices ✅ PASS

- **Configuration**: Environment variables for API keys (OPENAI_API_KEY), no hardcoded secrets
- **Error handling**: Explicit exception hierarchy with graceful degradation
- **Logging**: Structured logging planned (structlog library)
- **Dependencies**: All versions pinned in requirements.txt, virtual environment usage
- **Code organization**: Clear separation (api/, prompt/, validation/, storage/)

**Status**: Compliant - Python best practices integrated throughout design

### Quality Standards ✅ PASS

**Testing Requirements**:
- 80% minimum coverage: ✅ Specified
- Mock external dependencies: ✅ API mocking with respx/pytest-mock
- Fast execution (<10s unit tests): ✅ Performance goal defined
- Independent tests: ✅ No shared state, isolation enforced

**Documentation Requirements**:
- API documentation: ✅ Planned (docstrings, README)
- Architecture decisions: ✅ Documented in investigation plan
- Contracts: ✅ Will be formalized in Phase 1
- Success criteria: ✅ Defined in spec

**Code Quality**:
- Linting: ✅ ruff configured
- Type safety: ✅ Python 3.11+ with type hints
- Security: ✅ No secrets in code, env var management
- Performance: ✅ Goals defined (<30s generation)

### Overall Gate Status: ✅ PASS

All constitution principles are satisfied. No violations requiring justification. Component design aligns with LeSign architecture standards.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/ai-generation/
├── src/
│   ├── __init__.py
│   ├── generator.py         # Main AIImageGenerator class (public API)
│   ├── api/
│   │   ├── __init__.py
│   │   └── openai_client.py # OpenAI API wrapper
│   ├── prompt/
│   │   ├── __init__.py
│   │   └── optimizer.py     # Prompt engineering logic
│   ├── validation/
│   │   ├── __init__.py
│   │   └── validator.py     # Image quality validation
│   └── storage/
│       ├── __init__.py
│       └── manager.py       # File I/O operations
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Shared fixtures
│   ├── contract/
│   │   └── test_generator_contract.py
│   ├── integration/
│   │   ├── test_openai_integration.py
│   │   └── test_e2e_generation.py
│   └── unit/
│       ├── test_prompt_optimizer.py
│       ├── test_validator.py
│       └── test_storage_manager.py
├── config/
│   └── settings.py          # Configuration management
├── output/                  # Generated images (gitignored)
│   └── .gitkeep
├── .env.example             # Example environment variables
├── requirements.txt         # Pinned dependencies
├── requirements-dev.txt     # Development dependencies
├── pytest.ini               # Pytest configuration
├── pyproject.toml           # Ruff and mypy configuration
└── README.md                # Component documentation
```

**Structure Decision**: Single component structure within `backend/ai-generation/`. This is a standalone Python library component that will be called by the 3D Model Pipeline. The structure follows the modular component principle with clear separation between API client, business logic (prompt optimization, validation), and infrastructure concerns (storage).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
