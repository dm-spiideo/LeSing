<!--
SYNC IMPACT REPORT
==================
Version Change: INITIAL → 1.0.0
Rationale: Initial constitution creation for LeSign project

Added Sections:
- Core Principles (5 principles: Modular Components, Test-Driven Development, Clear Interfaces, Local-First POC, Python & Best Practices)
- Quality Standards (testing, coverage, documentation requirements)
- Development Workflow (TDD cycle, component development, integration)
- Governance (amendment process, versioning, compliance)

Templates Requiring Updates:
✅ plan-template.md - Constitution Check section aligns with modular component principles
✅ spec-template.md - User story prioritization aligns with independent testing principle
✅ tasks-template.md - Task organization by user story aligns with modular development

Follow-up TODOs:
- None - all placeholders filled based on project context
-->

# LeSign Constitution

## Core Principles

### I. Modular Components (NON-NEGOTIABLE)

Every component in the LeSign system MUST be:
- **Self-contained**: Independent operation with clear boundaries
- **Independently testable**: Can be validated in isolation
- **Well-documented**: Clear purpose, inputs, outputs, and contracts
- **Composable**: Can be orchestrated into automated pipelines

**Rationale**: The LeSign architecture depends on modular components to enable parallel development, independent scaling, and end-to-end automation. Breaking this principle undermines the entire system design.

**Example**: AI Image Generation, 3D Model Pipeline, and Printer Control are distinct modules with clear contracts, allowing teams to work in parallel and enabling the POC pipeline: text → image → 3D → print.

### II. Test-Driven Development (NON-NEGOTIABLE)

All code MUST follow the TDD discipline:
- Write tests FIRST before implementation
- Ensure tests FAIL before writing code
- Follow Red-Green-Refactor cycle strictly
- Minimum 80% code coverage for all components
- All public APIs MUST have tests

**Rationale**: TDD ensures code quality, catches bugs early, and creates living documentation. For an automated manufacturing platform like LeSign, reliability is critical—untested code is unacceptable.

**Testing Layers**:
- Unit tests for individual functions and classes
- Integration tests for component interactions (e.g., API calls)
- End-to-end tests for complete workflows (text → print)

### III. Clear Interfaces & Contracts

Every component MUST define:
- **Input contracts**: Expected data format, validation rules, error handling
- **Output contracts**: Guaranteed data format, success/failure states
- **API boundaries**: Well-documented endpoints, methods, or protocols
- **Error handling**: Explicit exception hierarchy and graceful degradation

**Rationale**: Clear contracts enable independent component development and prevent integration failures. In an automated pipeline, ambiguous interfaces cause cascading failures.

**Example**: 3D Model Pipeline accepts image files as input and produces G-code files as output, with explicit intermediate formats for 2D vectors and 3D models.

### IV. Local-First POC

For proof-of-concept implementations:
- Execute locally without cloud infrastructure
- Minimize dependencies and complexity
- Focus on architectural layers and boundaries
- Use simple, direct solutions over premature optimization

**Rationale**: POC validates concepts quickly with minimal overhead. Cloud infrastructure, distributed systems, and production features come later. Establish the foundation first.

**Example**: POC milestone uses OpenAI API with API keys (no custom ML infrastructure), local file storage (no cloud storage), and direct component communication (no message queues).

### V. Python & Best Practices

For Python-based components (backend/processing layer):
- **Configuration**: Environment variables for secrets, no hardcoded values
- **Error Handling**: Explicit exception hierarchy, comprehensive logging
- **Logging**: Structured JSON format, appropriate levels (DEBUG, INFO, WARNING, ERROR), no sensitive data
- **Dependencies**: Pin all versions, use virtual environments, document all dependencies
- **Code Organization**: Clear separation of concerns, Single Responsibility Principle, dependency injection for testability

**Rationale**: Consistent practices across components reduce cognitive load, improve maintainability, and prevent common security/reliability issues.

## Quality Standards

### Testing Requirements

- **Minimum Coverage**: 80% code coverage for all components
- **Mock External Dependencies**: All API calls, file I/O, and hardware interfaces must be mockable
- **Fast Execution**: Unit tests MUST complete in <10 seconds
- **Independent Tests**: Tests must not depend on execution order or shared state

### Documentation Requirements

- **API Documentation**: All public functions, classes, and endpoints documented
- **Architecture Decisions**: Major design choices documented in component README
- **Contracts**: Input/output formats explicitly documented
- **Success Criteria**: Every feature defines measurable success criteria

### Code Quality

- **Linting**: All code passes language-specific linters (e.g., ruff for Python)
- **Type Safety**: Use type hints where language supports (Python 3.11+)
- **Security**: No secrets in code, validate all inputs, handle errors gracefully
- **Performance**: Define and measure performance goals (e.g., <200ms API response time)

## Development Workflow

### TDD Cycle

1. **Write Test**: Define expected behavior in test code
2. **Verify Failure**: Run test and confirm it fails (Red)
3. **Implement**: Write minimal code to pass test
4. **Verify Success**: Run test and confirm it passes (Green)
5. **Refactor**: Improve code quality while keeping tests green
6. **Repeat**: Move to next test

### Component Development

1. **Define Contracts**: Document inputs, outputs, and behavior
2. **Setup Structure**: Create directory structure per plan
3. **Write Tests**: Contract, integration, and unit tests
4. **Implement**: Build component following TDD
5. **Validate**: Ensure independent operation and testability
6. **Document**: Update component README and API docs

### Integration

- Components integrate via well-defined contracts (files, APIs, protocols)
- Integration tests verify contract compliance
- Failures must be isolated and not cascade across components
- Each component must handle upstream/downstream failures gracefully

## Governance

### Amendment Process

This constitution can be amended through:
1. Proposal documenting change rationale and impact
2. Review of affected templates, components, and workflows
3. Approval from project maintainers
4. Migration plan for existing code/documentation
5. Version increment following semantic versioning

### Versioning Policy

- **MAJOR**: Backward-incompatible principle changes (e.g., removing TDD requirement)
- **MINOR**: New principle additions or material expansions
- **PATCH**: Clarifications, wording improvements, typo fixes

### Compliance Review

- All feature specifications must verify compliance with Core Principles
- All pull requests must pass constitution checks (see plan-template.md)
- Complexity that violates principles must be explicitly justified
- Project reviews should audit compliance quarterly

### Constitution Authority

This constitution supersedes all other practices, guidelines, and conventions. When conflicts arise, constitution principles take precedence. Any deviation MUST be documented and justified.

**Version**: 1.0.0 | **Ratified**: 2025-11-16 | **Last Amended**: 2025-11-16
