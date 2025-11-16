# Tasks: AI Image Generation for Name Signs

**Input**: Design documents from `/specs/001-ai-image-generation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contract.md

**Tests**: TDD is a core principle of this project (Constitution Principle II). All test tasks follow the Red-Green-Refactor cycle.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md project structure:
- Source code: `backend/ai-generation/src/`
- Tests: `backend/ai-generation/tests/`
- Config: `backend/ai-generation/config/`
- Output: `backend/ai-generation/output/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create backend/ai-generation/ directory structure per plan.md (src/, tests/, config/, output/)
- [ ] T002 Initialize Python project with pyproject.toml for Ruff and mypy configuration
- [ ] T003 [P] Create requirements.txt with pinned versions (openai==1.52.0, pydantic==2.9.2, pydantic-settings==2.5.2, pillow==10.4.0, python-dotenv==1.0.1, structlog==24.4.0, tenacity==9.0.0, httpx==0.27.2)
- [ ] T004 [P] Create requirements-dev.txt with testing dependencies (pytest==8.3.3, pytest-cov==5.0.0, pytest-mock==3.14.0, respx==0.21.1, vcrpy==6.0.1, ruff==0.7.0, mypy==1.13.0)
- [ ] T005 [P] Configure Ruff linting in pyproject.toml (target-version py312, select E/W/F/UP/B/SIM/I/N/S/C90, line-length 88)
- [ ] T006 [P] Configure pytest in pyproject.toml (testpaths, coverage settings, 80% minimum coverage)
- [ ] T007 [P] Configure mypy in pyproject.toml (python_version 3.12, strict mode, disallow_untyped_defs)
- [ ] T008 [P] Create .env.example with template environment variables (AI_GEN_OPENAI_API_KEY, AI_GEN_IMAGE_SIZE, AI_GEN_IMAGE_QUALITY, AI_GEN_STORAGE_PATH, AI_GEN_LOG_LEVEL)
- [ ] T009 [P] Create .gitignore to exclude .env, output/, __pycache__, .pytest_cache, htmlcov/
- [ ] T010 [P] Create backend/ai-generation/README.md with component overview and quickstart
- [ ] T011 Create backend/ai-generation/output/.gitkeep to track output directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T012 [P] Create exception hierarchy in backend/ai-generation/src/exceptions.py (AIGenerationError base, ValidationError, APIError with Auth/RateLimit/Service subclasses, QualityError, StorageError)
- [ ] T013 [P] Create Settings configuration class in backend/ai-generation/config/settings.py using pydantic-settings (openai_api_key, image_size, image_quality, storage_path, log_level, max_retries with env_prefix AI_GEN_)
- [ ] T014 [P] Create ImageRequest model in backend/ai-generation/src/models.py (request_id UUID, prompt 1-50 chars, style Literal, size Literal, quality Literal, timestamp, with Pydantic validators)
- [ ] T015 [P] Create ImageResult model in backend/ai-generation/src/models.py (request_id, image_path Path|None, status Literal, error str|None, metadata GenerationMetadata|None, timestamp, with status consistency validator)
- [ ] T016 [P] Create QualityValidation model in backend/ai-generation/src/models.py (request_id, image_path, file_exists, file_readable, format_valid, resolution_met, width, height, file_size_bytes, quality_score 0.0-1.0, validation_passed, timestamp)
- [ ] T017 [P] Create GenerationMetadata model in backend/ai-generation/src/models.py (model, original_prompt, optimized_prompt, generation_time_ms, image_size, image_format, file_size_bytes, quality_validation)
- [ ] T018 [P] Create backend/ai-generation/src/__init__.py exposing AIImageGenerator public API
- [ ] T019 [P] Create backend/ai-generation/tests/__init__.py
- [ ] T020 [P] Create shared test fixtures in backend/ai-generation/tests/conftest.py (test_settings fixture, mock_api_response fixture, sample_image_path fixture)
- [ ] T021 [P] Setup structlog logging configuration in backend/ai-generation/src/logging_config.py (JSON format, context processors, sensitive data filtering for API keys)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic Text-to-Image Generation (Priority: P1) 🎯 MVP

**Goal**: User provides a simple text prompt (e.g., "SARAH", "Welcome Home") and receives a name sign design image suitable for 3D printing

**Independent Test**: Can be fully tested by providing a text prompt and verifying that a valid image file is generated and saved locally. Success means an image exists, is readable, and contains visual representation of the requested text.

### Tests for User Story 1 (TDD - Write First)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T022 [P] [US1] Create unit test for prompt validation in backend/ai-generation/tests/unit/test_validator.py (valid prompts, empty prompts, too long, non-Latin characters)
- [ ] T023 [P] [US1] Create unit test for OpenAI client in backend/ai-generation/tests/unit/test_openai_client.py (successful response, rate limit, auth error, service error with mocked httpx)
- [ ] T024 [P] [US1] Create unit test for storage manager in backend/ai-generation/tests/unit/test_storage_manager.py (file naming, path generation, save operations with mocked file I/O)
- [ ] T025 [P] [US1] Create unit test for quality validator in backend/ai-generation/tests/unit/test_quality_validator.py (file exists check, resolution validation, format validation with mocked Pillow)
- [ ] T026 [US1] Create integration test for basic generation in backend/ai-generation/tests/integration/test_basic_generation.py (end-to-end flow with mocked OpenAI API using respx)
- [ ] T027 [US1] Create contract test for AIImageGenerator in backend/ai-generation/tests/contract/test_generator_contract.py (validate input/output contracts, exception types, ImageResult structure)

### Implementation for User Story 1

- [ ] T028 [P] [US1] Implement PromptValidator in backend/ai-generation/src/validation/validator.py (validate_prompt method checking length 1-50, non-empty, Latin chars only using regex)
- [ ] T029 [P] [US1] Implement OpenAIClient in backend/ai-generation/src/api/openai_client.py (generate_image_from_prompt method, error handling for 401/429/5xx, retry logic with tenacity exponential backoff)
- [ ] T030 [P] [US1] Implement StorageManager in backend/ai-generation/src/storage/manager.py (generate_filename with timestamp+request_id+slug, save_image method, save_metadata_json method, ensure output directory exists)
- [ ] T031 [P] [US1] Implement QualityValidator in backend/ai-generation/src/validation/quality_validator.py (validate_image method checking file_exists, file_readable with Pillow, format PNG/JPEG, resolution ≥1024x1024, calculate quality_score)
- [ ] T032 [US1] Implement AIImageGenerator.generate_image in backend/ai-generation/src/generator.py (create ImageRequest, call OpenAI client, save image, run quality validation, create ImageResult, handle all exceptions per contract)
- [ ] T033 [US1] Implement AIImageGenerator.__init__ in backend/ai-generation/src/generator.py (load Settings, initialize OpenAI client, storage manager, validators, configure logging)
- [ ] T034 [US1] Add input validation in AIImageGenerator.generate_image (validate prompt before API call, raise ValidationError for invalid inputs)
- [ ] T035 [US1] Add error handling and logging for US1 operations (log generation_started, image_saved, generation_completed events with structlog, mask API keys)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Styled Image Generation (Priority: P2)

**Goal**: User specifies a design style (modern, classic, playful) along with their text prompt to receive a name sign with appropriate aesthetic characteristics

**Independent Test**: Can be tested by generating images with different style parameters and verifying that the output images reflect the requested aesthetic through visual inspection or metadata

### Tests for User Story 2 (TDD - Write First)

- [ ] T036 [P] [US2] Create unit test for PromptOptimizer in backend/ai-generation/tests/unit/test_prompt_optimizer.py (optimize method with modern/classic/playful styles, verify style keywords added, original text preserved)
- [ ] T037 [P] [US2] Create integration test for styled generation in backend/ai-generation/tests/integration/test_styled_generation.py (generate with each style, verify metadata contains optimized_prompt and style)
- [ ] T038 [US2] Create contract test for style parameter in backend/ai-generation/tests/contract/test_generator_contract.py (validate style enum values, invalid style raises ValidationError)

### Implementation for User Story 2

- [ ] T039 [P] [US2] Create PromptOptimizer in backend/ai-generation/src/prompt/optimizer.py (optimize method applying style-specific keywords: modern="minimalist, clean lines", classic="elegant, traditional", playful="fun, colorful, rounded")
- [ ] T040 [US2] Update OpenAIClient to accept optimized prompts in backend/ai-generation/src/api/openai_client.py (modify generate_image_from_prompt to use optimized prompt parameter)
- [ ] T041 [US2] Integrate PromptOptimizer into AIImageGenerator.generate_image in backend/ai-generation/src/generator.py (call optimizer.optimize when style provided, track both original and optimized prompts in metadata)
- [ ] T042 [US2] Update GenerationMetadata to store both prompts in backend/ai-generation/src/models.py (ensure original_prompt and optimized_prompt both saved)
- [ ] T043 [US2] Add style validation in AIImageGenerator.generate_image (validate style is one of modern/classic/playful or None, raise ValidationError if invalid)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Quality Validation and Retry (Priority: P2)

**Goal**: When a generated image fails to meet quality criteria (resolution, clarity, printability), the system automatically detects this and either retries or reports the failure clearly

**Independent Test**: Can be tested by simulating or triggering low-quality image generation and verifying that the system correctly identifies the issue and takes appropriate action (retry or clear failure message)

### Tests for User Story 3 (TDD - Write First)

- [ ] T044 [P] [US3] Create unit test for retry logic in backend/ai-generation/tests/unit/test_retry_logic.py (test max 3 retries, exponential backoff timing, quality failure triggers retry, storage failure does not retry)
- [ ] T045 [P] [US3] Create integration test for quality retry in backend/ai-generation/tests/integration/test_quality_retry.py (mock low-resolution image, verify retry happens, verify max retries stops execution)
- [ ] T046 [US3] Create contract test for validation method in backend/ai-generation/tests/contract/test_generator_contract.py (test validate_image contract, QualityValidation structure, quality_score calculation)

### Implementation for User Story 3

- [ ] T047 [P] [US3] Implement AIImageGenerator.validate_image public method in backend/ai-generation/src/generator.py (accept image_path Path, return QualityValidation, handle FileNotFoundError)
- [ ] T048 [US3] Add retry logic for quality failures in AIImageGenerator.generate_image (detect validation_passed=False, retry with modified prompt up to max_retries=3, track retry count in logs)
- [ ] T049 [US3] Add retry logic for API failures in OpenAIClient (handle RateLimitError with exponential backoff 2s/4s/8s, handle ServiceError with fixed delay 5s, max 3 attempts)
- [ ] T050 [US3] Update error handling to differentiate retryable vs non-retryable errors (ValidationError/AuthenticationError/StorageError=no retry, RateLimitError/ServiceError/QualityError=retry with backoff)
- [ ] T051 [US3] Add comprehensive error logging for retry attempts (log retry_attempt event with attempt_number, error_type, backoff_seconds, use structlog)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T052 [P] Add type hints to all public and private functions across all modules (use Python 3.12 syntax: native generics, union types with |)
- [ ] T053 [P] Add comprehensive docstrings to all public classes and methods (Google-style format per CODE_GUIDELINES.md)
- [ ] T054 [P] Create unit tests for edge cases in backend/ai-generation/tests/unit/test_edge_cases.py (storage full, concurrent requests, extremely long prompts, special characters)
- [ ] T055 Run ruff check --fix . to auto-fix linting issues in backend/ai-generation/
- [ ] T056 Run ruff format . to format all code in backend/ai-generation/
- [ ] T057 Run mypy src/ to verify type checking passes in backend/ai-generation/
- [ ] T058 Run pytest --cov=src --cov-fail-under=80 to verify 80% minimum coverage requirement
- [ ] T059 [P] Update backend/ai-generation/README.md with usage examples, API reference, and troubleshooting
- [ ] T060 Validate quickstart.md examples work end-to-end (run example code, verify outputs match documentation)
- [ ] T061 [P] Add security hardening (verify no API keys in logs, validate file paths prevent directory traversal, add rate limit warnings)
- [ ] T062 Create example integration script in backend/ai-generation/examples/basic_usage.py demonstrating User Story 1 scenario
- [ ] T063 [P] Create example integration script in backend/ai-generation/examples/styled_usage.py demonstrating User Story 2 scenario
- [ ] T064 [P] Create example integration script in backend/ai-generation/examples/validation_usage.py demonstrating User Story 3 scenario

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (US1 → US2 → US3)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories ✅ INDEPENDENT
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 but independently testable (can generate styled images without US1 tests passing) ✅ INDEPENDENT
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Uses validation from US1 but adds retry logic, independently testable ✅ INDEPENDENT

### Within Each User Story

- Tests MUST be written FIRST and FAIL before implementation (TDD Red-Green-Refactor)
- Unit tests [P] can run in parallel (different test files)
- Integration/contract tests run after unit tests written
- Models and utilities [P] can be implemented in parallel after tests written
- Core implementation integrates components after individual pieces tested
- Story complete and all tests passing before moving to next priority

### Parallel Opportunities

**Setup Phase (Phase 1)**:
- T003, T004, T005, T006, T007, T008, T009, T010 can all run in parallel (different files)

**Foundational Phase (Phase 2)**:
- T012, T013, T014, T015, T016, T017, T018, T019, T020, T021 can all run in parallel (different files)

**User Story 1 Tests**:
- T022, T023, T024, T025 can run in parallel (different test files)

**User Story 1 Implementation**:
- T028, T029, T030, T031 can run in parallel (different modules)

**User Story 2 Tests**:
- T036, T037 can run in parallel

**User Story 3 Tests**:
- T044, T045 can run in parallel

**Cross-Story Parallelization**:
- Once Foundational phase completes:
  - Developer A: Work on User Story 1 (T022-T035)
  - Developer B: Work on User Story 2 (T036-T043)
  - Developer C: Work on User Story 3 (T044-T051)
- Stories integrate at completion

**Polish Phase**:
- T052, T053, T054, T059, T061, T062, T063, T064 can run in parallel (different files/concerns)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (TDD - write tests first):
Task T022: "Create unit test for prompt validation in backend/ai-generation/tests/unit/test_validator.py"
Task T023: "Create unit test for OpenAI client in backend/ai-generation/tests/unit/test_openai_client.py"
Task T024: "Create unit test for storage manager in backend/ai-generation/tests/unit/test_storage_manager.py"
Task T025: "Create unit test for quality validator in backend/ai-generation/tests/unit/test_quality_validator.py"

# Verify tests FAIL (Red phase of TDD)

# Launch all implementation components for User Story 1 together:
Task T028: "Implement PromptValidator in backend/ai-generation/src/validation/validator.py"
Task T029: "Implement OpenAIClient in backend/ai-generation/src/api/openai_client.py"
Task T030: "Implement StorageManager in backend/ai-generation/src/storage/manager.py"
Task T031: "Implement QualityValidator in backend/ai-generation/src/validation/quality_validator.py"

# Then integrate in generator (T032, T033)
# Then verify tests PASS (Green phase of TDD)
# Then refactor (Refactor phase of TDD)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T011)
2. Complete Phase 2: Foundational (T012-T021) - CRITICAL - blocks all stories
3. Complete Phase 3: User Story 1 (T022-T035)
   - Write tests FIRST (T022-T027) ✅ RED
   - Verify tests FAIL
   - Implement features (T028-T035) ✅ GREEN
   - Verify tests PASS
   - Refactor if needed ✅ REFACTOR
4. **STOP and VALIDATE**: Test User Story 1 independently with real OpenAI API
5. Deploy/demo if ready - basic text-to-image generation working!

### Incremental Delivery

1. Complete Setup + Foundational (T001-T021) → Foundation ready
2. Add User Story 1 (T022-T035) → Test independently → Deploy/Demo (**MVP!** - basic generation works)
3. Add User Story 2 (T036-T043) → Test independently → Deploy/Demo (now with styles!)
4. Add User Story 3 (T044-T051) → Test independently → Deploy/Demo (now with retry logic!)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T021)
2. Once Foundational is done:
   - **Developer A**: User Story 1 (T022-T035) - Basic generation
   - **Developer B**: User Story 2 (T036-T043) - Style support
   - **Developer C**: User Story 3 (T044-T051) - Retry logic
3. Stories complete and integrate independently
4. Final integration and polish together (T052-T064)

---

## TDD Red-Green-Refactor Checklist

For each user story:

- ✅ **RED**: Write tests first (T022-T027 for US1, T036-T038 for US2, T044-T046 for US3)
- ✅ **RED**: Run pytest and verify tests FAIL (no implementation yet)
- ✅ **GREEN**: Implement minimum code to make tests pass
- ✅ **GREEN**: Run pytest and verify tests PASS
- ✅ **REFACTOR**: Improve code quality while keeping tests green
- ✅ **VERIFY**: Run pytest --cov to check coverage increases toward 80% minimum

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **TDD is mandatory**: Verify tests fail before implementing (Constitution Principle II)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Run ruff check and ruff format before committing
- Target 80% minimum test coverage (enforced in CI, Constitution requirement)
- All exceptions must follow hierarchy in backend/ai-generation/src/exceptions.py
- All configuration via environment variables with AI_GEN_ prefix
- Use structured logging (structlog) with JSON format, mask sensitive data
