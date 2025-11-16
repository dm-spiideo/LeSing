# Quickstart: Printer Control

**Feature**: 003-printer-control
**Date**: 2025-11-16
**Purpose**: Get up and running with printer control development

## Prerequisites

- Python 3.12 installed (`python3 --version`)
- UV package manager installed (`uv --version`)
- Bambu Lab H2D printer on local network (LAN mode)
- Printer credentials: IP address, serial number, access code

## Setup (5 minutes)

### 1. Environment Setup

```bash
# Navigate to printer control directory
cd backend/printer-control

# Create virtual environment with Python 3.12
uv venv --python 3.12

# Activate virtual environment (optional, uv run handles this)
source .venv/bin/activate  # macOS/Linux

# Install dependencies
uv sync

# Verify installation
uv run python --version  # Should show Python 3.12.x
uv run pytest --version  # Should show pytest
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your printer credentials
# Required variables:
#   PRINTER_IP=192.168.1.200
#   PRINTER_SERIAL=AC12345678
#   PRINTER_ACCESS_CODE=12345678
nano .env  # or use your preferred editor
```

**Finding Printer Credentials** (Bambu Lab H2D):
1. On printer touchscreen: Settings → WLAN
2. Note **IP Address** (e.g., 192.168.1.200)
3. Note **Access Code** (8-digit code)
4. Serial number is on printer label or in Settings → Device

### 3. Validate Connection

```bash
# Run connection test (will be created in Phase 1)
uv run python -m printer_control.tests.validate_connection

# Expected output:
# ✓ Connecting to printer at 192.168.1.200...
# ✓ MQTT connection established
# ✓ FTP connection established
# ✓ Printer status: idle
# ✓ Connection test passed
```

## Development Workflow

### Run Tests

```bash
# Run all tests
uv run pytest

# Run specific test suite
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/contract/

# Run with coverage
uv run pytest --cov=src --cov-report=html --cov-report=term

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Linting & Formatting

```bash
# Run linter
ruff check src/ tests/

# Auto-fix linting issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/

# Type check
mypy src/
```

### TDD Cycle (Example)

```bash
# 1. Write failing test
cat > tests/unit/test_new_feature.py
# ... write test ...

# 2. Verify test fails (Red)
uv run pytest tests/unit/test_new_feature.py
# Expected: Test fails

# 3. Implement minimal code (Green)
# Edit src/...

# 4. Verify test passes
uv run pytest tests/unit/test_new_feature.py
# Expected: Test passes

# 5. Refactor while keeping tests green
# Improve code quality

# 6. Run full test suite
uv run pytest
```

## Quick Reference

### Project Structure

```
backend/printer-control/
├── src/
│   ├── printer_agent.py       # Submit jobs, get status
│   ├── hardware_interface.py  # MQTT/FTP communication
│   ├── job_queue.py           # Queue management
│   ├── models.py              # Pydantic data models
│   └── exceptions.py          # Error hierarchy
├── tests/
│   ├── contract/              # Interface validation
│   ├── integration/           # Component interaction
│   └── unit/                  # Isolated tests
└── .env                       # Local configuration (gitignored)
```

### Key Commands

| Task | Command |
|------|---------|
| Install dependencies | `uv sync` |
| Run tests | `uv run pytest` |
| Coverage report | `uv run pytest --cov=src --cov-report=html` |
| Lint code | `ruff check .` |
| Format code | `ruff format .` |
| Type check | `mypy src/` |
| Run module | `uv run python -m printer_control.agent` |

### Common Tasks

**Submit a Print Job** (after implementation):
```python
from pathlib import Path
from printer_control.printer_agent import PrinterAgent
from printer_control.models import PrintRequest

agent = PrinterAgent()
result = agent.submit_job(
    file_path=Path("/path/to/file.gcode"),
    job_id="job_001"
)
print(f"Status: {result.status}")
print(f"Queue position: {result.queue_position}")
```

**Query Job Status**:
```python
status = agent.get_job_status("job_001")
print(f"Progress: {status.progress_percent}%")
print(f"Remaining: {status.remaining_time_minutes} min")
```

**Cancel Job**:
```python
success = agent.cancel_job("job_001")
```

### Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'printer_control'`
- **Solution**: Ensure you're in `backend/printer-control` directory and run `uv sync`

**Issue**: `Connection refused` when testing
- **Solution**:
  1. Verify printer is on and connected to network
  2. Check `.env` has correct IP address
  3. Ping printer: `ping 192.168.1.200`
  4. Ensure LAN mode is enabled on printer

**Issue**: `Authentication failed`
- **Solution**:
  1. Verify access code in `.env` matches printer Settings → WLAN → Access Code
  2. Access code changes if printer is reset

**Issue**: `Tests run slow`
- **Solution**:
  1. Unit tests should use mocks (no real printer connection)
  2. Integration tests can be skipped with `pytest -m "not integration"`
  3. Check for accidental real network calls in unit tests

## Next Steps

### Phase 1: Hardware Interface MVP (Week 1-2)

**Tasks**:
1. ✅ Set up development environment
2. ✅ Configure printer credentials
3. ✅ Validate connection
4. ▢ Implement `BambuHardwareInterface`
5. ▢ Implement G-code → 3MF conversion
6. ▢ Write contract tests
7. ▢ Write unit tests
8. ▢ Manual H2D testing
9. ▢ Document H2D-specific behaviors

**Start Here**:
```bash
# Create contract tests first (TDD)
touch tests/contract/test_hardware_interface.py

# Write test for connect() method
# Then implement in src/hardware_interface.py
```

### Phase 2: Printer Agent & Integration (Week 2-3)

**After Phase 1 complete**, implement:
1. PrinterAgent orchestration
2. Pydantic models
3. Exception hierarchy
4. Integration tests

See [plan.md](./plan.md) for detailed phase breakdown.

## Resources

- **Spec**: [spec.md](./spec.md) - Requirements and acceptance criteria
- **Plan**: [plan.md](./plan.md) - Implementation approach
- **Research**: [research.md](./research.md) - Technical decisions
- **Data Model**: [data-model.md](./data-model.md) - Entity definitions
- **Contracts**: [contracts/](./contracts/) - JSON schemas
- **Backend Guidelines**: [../../backend/CODE_GUIDELINES.md](../../backend/CODE_GUIDELINES.md)

## Getting Help

- **Constitution**: [../../.specify/memory/constitution.md](../../.specify/memory/constitution.md) - Core principles
- **bambulabs-api Docs**: https://bambutools.github.io/bambulabs_api/
- **Bambu Lab Wiki**: https://wiki.bambulab.com/
- **Project Issues**: Create GitHub issue for questions/bugs
