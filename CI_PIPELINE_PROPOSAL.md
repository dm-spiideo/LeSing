# GitHub Actions CI Pipeline for AI Image Generation Component

## Overview

Implement a simple, automated continuous integration pipeline for the Python backend project (`backend/ai-generation`) using GitHub Actions.

## Current State

The project already has excellent development practices:
- **Test Suite**: 95 tests with 91.43% coverage (exceeds 80% requirement)
- **Linting**: Ruff configured with comprehensive rules
- **Type Checking**: mypy in strict mode
- **Python Version**: Requires 3.11+
- **Dependencies**: Managed via requirements.txt and pyproject.toml

## Proposed CI Pipeline

### Workflow Triggers
- **Push**: Run on all pushes to any branch
- **Pull Requests**: Run on all PRs targeting main/master

### Jobs

#### 1. **Test Job** (Python 3.11 and 3.12)
- Set up Python environment
- Install dependencies (requirements.txt + requirements-dev.txt)
- Run pytest with coverage
- Upload coverage reports
- **Exit Criteria**: All tests pass, coverage ≥ 80%

#### 2. **Lint Job**
- Run ruff check on src/ and tests/
- **Exit Criteria**: No linting errors

#### 3. **Type Check Job**
- Run mypy on src/
- **Exit Criteria**: All type checks pass

### Working Directory
All jobs run in `backend/ai-generation/` directory

### Environment Variables
- Tests that require OpenAI API should be mocked (already done with respx/vcrpy)
- No secrets needed for basic CI

## Benefits

1. **Quality Assurance**: Catch bugs before merging
2. **Consistency**: Same checks run for everyone
3. **Fast Feedback**: Know within minutes if changes break anything
4. **Documentation**: CI badge shows project health
5. **Simplicity**: Uses existing tools, no new dependencies

## Implementation Approach

### Phase 1 (This Issue)
- Create `.github/workflows/python-ci.yml`
- Configure test, lint, and type-check jobs
- Test on Python 3.11 and 3.12
- Add status badge to README

### Phase 2 (Future)
- Add caching for pip dependencies (speed improvement)
- Add test result reporting
- Consider branch protection rules requiring CI to pass

## Technical Specifications

### Workflow File Location
```
.github/workflows/python-ci.yml
```

### Example Job Structure
```yaml
name: Python CI

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    defaults:
      run:
        working-directory: backend/ai-generation
    steps:
      - Checkout code
      - Setup Python
      - Install dependencies
      - Run tests with coverage

  lint:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend/ai-generation
    steps:
      - Checkout code
      - Setup Python
      - Install dev dependencies
      - Run ruff check

  type-check:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend/ai-generation
    steps:
      - Checkout code
      - Setup Python
      - Install dependencies
      - Run mypy
```

## Success Criteria

- [ ] CI workflow runs automatically on push and PR
- [ ] Tests pass on Python 3.11 and 3.12
- [ ] Linting checks pass
- [ ] Type checking passes
- [ ] Total workflow time < 5 minutes
- [ ] Status badge added to README
- [ ] Documentation updated with CI information

## Questions to Consider

1. Should we fail the build if coverage drops below 80%? (Already configured in pyproject.toml)
2. Do we want to generate coverage reports as artifacts?
3. Should we add automatic dependency security scanning (e.g., pip-audit)?
4. Do we need separate workflows for different Python components in the future?

## Estimated Effort

- **Implementation**: 1-2 hours
- **Testing**: 30 minutes
- **Documentation**: 30 minutes
- **Total**: ~2-3 hours

## Dependencies

None - can be implemented immediately

## Related Documentation

- GitHub Actions: https://docs.github.com/en/actions
- Python CI best practices: https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python
