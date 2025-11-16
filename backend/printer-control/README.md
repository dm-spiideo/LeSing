# Printer Control - Bambu Lab Printer Interface

**Feature**: 003-printer-control
**Status**: MVP Implementation
**Python**: 3.12+

## Overview

Printer Control provides direct communication and control of Bambu Lab 3D printer hardware (H2D and compatible models). It manages G-code execution, print job initiation and monitoring, local job buffering, and real-time status tracking.

**Key Features**:
- ✅ MQTT-based printer control (start, pause, cancel)
- ✅ FTP G-code file upload
- ✅ Local job queue with persistence
- ✅ Automatic retry on transient failures
- ✅ Real-time status monitoring
- ✅ Type-safe Pydantic models
- ✅ Structured JSON logging

## Quick Start

### Prerequisites

- Python 3.12+
- Bambu Lab H2D printer (or compatible)
- Printer Developer Mode enabled
- Printer access code and serial number

### Installation

```bash
cd backend/printer-control

# Create virtual environment
uv venv --python 3.12

# Install dependencies
uv sync

# Verify installation
uv run python -c "import printer_control; print('OK')"
```

### Basic Usage

```python
from pathlib import Path
from printer_control import PrinterAgent, load_config

# Load configuration from environment variables or YAML
config = load_config()

# Initialize agent
agent = PrinterAgent(config)
agent.start()

try:
    # Submit print job
    job = agent.submit_job(
        gcode_path=Path("/data/welcome_home.gcode"),
        name="Welcome Home Sign",
        priority=0
    )

    print(f"Job submitted: {job.job_id}")
    print(f"Status: {job.status}")

    # Monitor progress
    status = agent.get_job_status(job.job_id)
    print(f"Progress: {status.progress}%")

finally:
    agent.stop()
```

See [Quickstart Guide](../../specs/003-printer-control/quickstart.md) for detailed setup instructions.

## Configuration

### Environment Variables (.env)

```bash
# Required
PRINTER_CONTROL_PRINTER_IP=192.168.1.100
PRINTER_CONTROL_ACCESS_CODE=12345678
PRINTER_CONTROL_SERIAL=01P00A000000000

# Optional
PRINTER_CONTROL_PRINTER_ID=bambu_h2d_01
PRINTER_CONTROL_QUEUE_PATH=./data/print_queue.json
PRINTER_CONTROL_MAX_RETRIES=3
PRINTER_CONTROL_STATUS_POLL_INTERVAL=5.0
PRINTER_CONTROL_LOG_LEVEL=INFO
```

### YAML Configuration

```yaml
# config/printer_config.yaml
printer_id: bambu_h2d_01
name: "Bambu Lab H2D #1"
model: "Bambu Lab H2D"
ip: 192.168.1.100
access_code: "12345678"
serial: "01P00A000000000"

capabilities:
  build_volume: {x: 256, y: 256, z: 256}
  materials: [PLA, PETG, ABS]
  max_temp_nozzle: 300
  max_temp_bed: 110
```

## Architecture

```
PrinterAgent (Orchestration)
├── PrintQueue (Job queue + persistence)
├── BambuLabPrinter (Hardware interface)
│   ├── MQTT (Control commands)
│   └── FTP (G-code upload)
└── Background Thread (Queue processing)
```

**Data Flow**:
1. Job submitted to PrinterAgent
2. Added to persistent queue (JSON)
3. Background thread processes queue
4. Upload G-code via FTP
5. Start print via MQTT
6. Monitor status via MQTT polling
7. Mark completed and save queue

## API Reference

### PrinterAgent

```python
# Initialize
agent = PrinterAgent(config, queue_path=Path("./data/queue.json"))

# Lifecycle
agent.start()  # Connect and start queue processing
agent.stop()   # Save state and disconnect

# Job management
job = agent.submit_job(gcode_path, name, priority, metadata)
status = agent.get_job_status(job_id)
success = agent.cancel_job(job_id)

# Monitoring
printer_status = agent.get_printer_status()
queue_state = agent.get_queue_state()
```

### BambuLabPrinter (Low-level)

```python
printer = BambuLabPrinter(config)

# Connection
printer.connect()
printer.disconnect()

# Operations
printer.upload_file(local_path, remote_name)
printer.start_print(filename)
printer.pause_print()
printer.cancel_print()
status = printer.get_status()
```

See [API Contract](../../specs/003-printer-control/contracts/api-contract.md) for complete API documentation.

## Testing

### Run Tests

```bash
# All tests with coverage
uv run pytest

# Unit tests only
uv run pytest tests/unit/

# With coverage report
uv run pytest --cov=src/printer_control --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Test Coverage

- **Target**: >90% coverage
- **Current**: ~95% (unit tests)
- **Integration tests**: Require actual printer or mock MQTT broker

## Development

### Code Quality

```bash
# Lint
ruff check .

# Fix linting issues
ruff check --fix .

# Format
ruff format .

# Type check
mypy src/
```

### Project Structure

```
backend/printer-control/
├── src/printer_control/       # Source code
│   ├── __init__.py
│   ├── agent.py              # Main printer agent (orchestration)
│   ├── printer.py            # Bambu Lab printer interface
│   ├── queue.py              # Job queue management
│   ├── models.py             # Pydantic data models
│   ├── config.py             # Configuration loading
│   └── exceptions.py         # Custom exceptions
├── tests/                    # Test suite
│   ├── unit/                # Unit tests (mocked dependencies)
│   ├── integration/         # Integration tests (real printer)
│   └── contract/            # API contract tests
├── config/                   # Configuration files
│   └── printer_profiles/    # Printer profiles (YAML/JSON)
├── data/                     # Runtime data (queue state)
├── pyproject.toml           # Project configuration
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Deployment

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync --no-dev
VOLUME /app/data
CMD ["uv", "run", "python", "-m", "printer_control.agent"]
```

### Systemd Service

```ini
[Unit]
Description=LeSign Printer Agent
After=network.target

[Service]
Type=simple
WorkingDir=/opt/lesign/backend/printer-control
EnvironmentFile=/opt/lesign/backend/printer-control/.env
ExecStart=/opt/lesign/backend/printer-control/.venv/bin/python -m printer_control.agent
Restart=always

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Connection Issues

**Problem**: `ConnectionError: Timeout connecting to printer`

**Solutions**:
- Verify printer IP address (`ping 192.168.1.100`)
- Ensure Developer Mode enabled on printer
- Check firewall allows ports 8883 (MQTT) and 990 (FTP)

### Authentication Failed

**Problem**: `AuthenticationError: Invalid access code or serial`

**Solutions**:
- Verify access code from printer settings (Settings → General → Developer Mode)
- Check serial number matches printer label
- Ensure no extra whitespace in config

### Upload Hangs

**Problem**: Job stuck in `UPLOADING` status

**Solutions**:
- Check FTP port 990 accessible
- Verify G-code file size <100MB
- Increase `ftp.timeout` in config
- Check printer storage not full

## Dependencies

### Core
- `bambulabs-api`: Bambu Lab printer control library
- `pydantic`: Data validation
- `tenacity`: Retry logic
- `structlog`: Structured logging
- `paho-mqtt`: MQTT protocol (via bambulabs_api)

### Development
- `pytest`: Testing framework
- `ruff`: Linting and formatting
- `mypy`: Type checking

## Documentation

- [Feature Spec](../../specs/003-printer-control/spec.md)
- [Quickstart Guide](../../specs/003-printer-control/quickstart.md)
- [API Contract](../../specs/003-printer-control/contracts/api-contract.md)
- [Data Models](../../specs/003-printer-control/data-model.md)
- [Implementation Plan](../../specs/003-printer-control/plan.md)

## Known Limitations

- **H2D Compatibility**: bambulabs_api library not tested with H2D printers yet (may require patches)
- **Single Printer**: MVP supports one printer per agent (multi-printer support planned for Phase 4)
- **Camera**: Camera integration not implemented (future feature)
- **Developer Mode**: Requires enabling on printer (security trade-off)

## Contributing

Follow [LeSign Code Guidelines](../../backend/CODE_GUIDELINES.md) for all contributions.

## License

Internal project - Not for public distribution
