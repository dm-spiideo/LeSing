# Quickstart: Printer Control

**Feature**: 003-printer-control
**Time to first print**: ~15 minutes

## Prerequisites

- ✅ Python 3.12+
- ✅ Bambu Lab H2D printer on local network
- ✅ Printer access code (from printer settings)
- ✅ Printer serial number
- ✅ G-code file from slicer (Feature 002)

---

## Step 1: Enable Printer Developer Mode

Bambu Lab printers require Developer Mode for local API access.

### On Printer Touchscreen:

1. Go to **Settings** → **General**
2. Scroll to **Developer Mode**
3. Toggle **ON**
4. Note the **Access Code** (8-character alphanumeric)
5. Note the **Serial Number** (starts with `01P00A...`)
6. Note the printer's **IP address** (Settings → Network)

**Security Note**: Developer Mode opens MQTT and FTP ports. Only enable on trusted networks.

---

## Step 2: Install Dependencies

```bash
cd backend/printer-control

# Create virtual environment
uv venv --python 3.12

# Install dependencies
uv sync

# Verify installation
uv run python -c "import printer_control; print('OK')"
```

---

## Step 3: Configure Printer

### Option A: Environment Variables (.env)

Create `.env` file in `backend/printer-control/`:

```bash
# Printer connection
PRINTER_CONTROL_PRINTER_IP=192.168.1.100
PRINTER_CONTROL_ACCESS_CODE=12345678
PRINTER_CONTROL_SERIAL=01P00A000000000

# Queue settings
PRINTER_CONTROL_QUEUE_PATH=./data/print_queue.json
PRINTER_CONTROL_MAX_RETRIES=3

# Monitoring
PRINTER_CONTROL_STATUS_POLL_INTERVAL=5.0
PRINTER_CONTROL_LOG_LEVEL=INFO
```

### Option B: Configuration File (config.yaml)

Create `config/printer_config.yaml`:

```yaml
printer_id: bambu_h2d_01
name: "Bambu Lab H2D #1"
model: "Bambu Lab H2D"
ip: 192.168.1.100
access_code: "12345678"
serial: "01P00A000000000"

capabilities:
  build_volume:
    x: 256
    y: 256
    z: 256
  materials:
    - PLA
    - PETG
    - ABS
  max_temp_nozzle: 300
  max_temp_bed: 110
  has_filament_sensor: true
  has_camera: true

mqtt:
  port: 8883
  use_tls: true
  keepalive: 60
  timeout: 30

ftp:
  port: 990
  use_tls: true
  timeout: 30

status_poll_interval: 5.0
```

---

## Step 4: Test Printer Connection

```bash
# Run connection test
uv run python -m printer_control.test_connection

# Expected output:
# ✓ Connecting to 192.168.1.100...
# ✓ MQTT connection established
# ✓ Printer online: Bambu Lab H2D (firmware 01.09.00.00)
# ✓ Status: IDLE, ready for jobs
```

**Troubleshooting**:
- **Connection timeout**: Check IP address, ensure printer on same network
- **Authentication failed**: Verify access code and serial number
- **Port unreachable**: Ensure Developer Mode enabled on printer

---

## Step 5: Submit First Print Job

### Example: Basic Usage

```python
from pathlib import Path
from printer_control import PrinterAgent, PrinterConfig
from printer_control.config import load_config

# Load configuration
config = load_config()  # Reads from .env or config.yaml

# Initialize agent
agent = PrinterAgent(config)
agent.start()

try:
    # Submit print job
    job = agent.submit_job(
        gcode_path=Path("/path/to/welcome_home.gcode"),
        name="Welcome Home Sign",
        priority=0
    )

    print(f"✓ Job submitted: {job.job_id}")
    print(f"  Status: {job.status}")
    print(f"  Queue position: 1")

    # Agent automatically processes queue in background
    # Monitor via get_job_status() or wait for completion

finally:
    agent.stop()
```

### Example: Monitor Progress

```python
import time
from printer_control import PrintJobStatus

# Submit job (see above)
job = agent.submit_job(...)

# Monitor progress
print("Monitoring print progress...")
while True:
    job = agent.get_job_status(job.job_id)

    if job.status == PrintJobStatus.PRINTING:
        print(f"  Progress: {job.progress:.1f}% (Layer {job.current_layer}/{job.total_layers})")
        print(f"  Time remaining: {job.time_remaining_seconds // 60} min")

    elif job.status in {PrintJobStatus.COMPLETED, PrintJobStatus.FAILED, PrintJobStatus.ERROR}:
        print(f"  Final status: {job.status}")
        if job.error_message:
            print(f"  Error: {job.error_message}")
        break

    time.sleep(5)  # Poll every 5 seconds
```

---

## Step 6: Check Queue Status

```python
# Get queue state
queue = agent.get_queue_state()

print(f"Queue Status:")
print(f"  Pending: {len(queue.pending)} jobs")
print(f"  Active: {len(queue.active)} jobs")
print(f"  Completed: {len(queue.completed)} jobs")
print(f"  Failed: {len(queue.failed)} jobs")

# List pending jobs
for job_id in queue.pending:
    job = agent.get_job_status(job_id)
    print(f"  - {job.name} (priority: {job.priority})")
```

---

## Step 7: Monitor Printer Status

```python
# Get real-time printer status
status = agent.get_printer_status()

print(f"Printer Status:")
print(f"  State: {status.state}")
print(f"  Online: {status.online}")
print(f"  Nozzle: {status.nozzle_temp.current}°C / {status.nozzle_temp.target}°C")
print(f"  Bed: {status.bed_temp.current}°C / {status.bed_temp.target}°C")

if status.current_job_id:
    print(f"  Current job: {status.current_job_id} ({status.progress}%)")
```

---

## Advanced Usage

### Multiple Jobs

```python
# Submit multiple jobs (queued automatically)
jobs = []
for gcode_file in Path("/data/gcode/").glob("*.gcode"):
    job = agent.submit_job(
        gcode_path=gcode_file,
        name=gcode_file.stem,
        priority=0
    )
    jobs.append(job)

print(f"Submitted {len(jobs)} jobs to queue")

# Jobs will be processed in FIFO order
```

### Priority Jobs (Rush Orders)

```python
# High-priority job (jumps queue)
rush_job = agent.submit_job(
    gcode_path=Path("/data/urgent.gcode"),
    name="Rush Order",
    priority=10  # Higher = more urgent
)

print(f"Rush job submitted (priority {rush_job.priority})")
```

### Cancel Job

```python
# Cancel pending or active job
success = agent.cancel_job(job.job_id)

if success:
    print("Job cancelled successfully")
else:
    print("Job not found or already completed")
```

### Error Handling

```python
from printer_control import ConnectionError, UploadError, QueueError

try:
    job = agent.submit_job(Path("/data/test.gcode"))

except FileNotFoundError:
    print("G-code file not found")
except ValidationError as e:
    print(f"Invalid G-code file: {e.message}")
except QueueError as e:
    print(f"Queue error: {e.message}")
except ConnectionError as e:
    print(f"Printer offline: {e.message}")
```

---

## Production Deployment

### Systemd Service (Linux)

Create `/etc/systemd/system/printer-agent.service`:

```ini
[Unit]
Description=LeSign Printer Agent
After=network.target

[Service]
Type=simple
User=lesign
WorkingDir=/opt/lesign/backend/printer-control
EnvironmentFile=/opt/lesign/backend/printer-control/.env
ExecStart=/opt/lesign/backend/printer-control/.venv/bin/python -m printer_control.agent
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable printer-agent
sudo systemctl start printer-agent
sudo systemctl status printer-agent
```

### Docker Container

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --no-dev

# Copy source code
COPY src/ ./src/

# Mount volume for queue state
VOLUME /app/data

# Run agent
CMD ["uv", "run", "python", "-m", "printer_control.agent"]
```

Build and run:
```bash
docker build -t lesign-printer-agent .
docker run -d \
  --name printer-agent \
  -v /data/queue:/app/data \
  -e PRINTER_CONTROL_PRINTER_IP=192.168.1.100 \
  -e PRINTER_CONTROL_ACCESS_CODE=12345678 \
  -e PRINTER_CONTROL_SERIAL=01P00A000000000 \
  lesign-printer-agent
```

---

## Monitoring & Logging

### View Logs

```bash
# Real-time logs
tail -f /var/log/printer-agent.log

# JSON structured logs
cat /var/log/printer-agent.log | jq '.event, .job_id, .status'
```

### Example Log Output

```json
{"event": "agent_started", "timestamp": "2025-11-16T12:00:00Z", "printer_id": "bambu_h2d_01"}
{"event": "job_submitted", "timestamp": "2025-11-16T12:01:00Z", "job_id": "job_001", "queue_depth": 1}
{"event": "job_uploading", "timestamp": "2025-11-16T12:01:05Z", "job_id": "job_001", "file_size_mb": 2.5}
{"event": "job_starting", "timestamp": "2025-11-16T12:01:30Z", "job_id": "job_001"}
{"event": "job_printing", "timestamp": "2025-11-16T12:02:00Z", "job_id": "job_001", "progress": 0.0}
{"event": "job_progress", "timestamp": "2025-11-16T12:10:00Z", "job_id": "job_001", "progress": 25.0, "layer": 70}
{"event": "job_completed", "timestamp": "2025-11-16T13:00:00Z", "job_id": "job_001", "duration_seconds": 3540}
```

---

## Troubleshooting

### Printer Not Found

**Symptom**: `ConnectionError: Timeout connecting to printer`

**Solutions**:
- ✅ Verify printer IP address (`ping 192.168.1.100`)
- ✅ Ensure printer on same network/VLAN
- ✅ Check firewall rules (allow ports 8883, 990)
- ✅ Verify Developer Mode enabled on printer

### Authentication Failed

**Symptom**: `AuthenticationError: Invalid access code or serial`

**Solutions**:
- ✅ Verify access code from printer settings (case-sensitive)
- ✅ Verify serial number matches printer label
- ✅ Ensure no extra whitespace in config

### Upload Hangs

**Symptom**: Job stuck in `UPLOADING` state

**Solutions**:
- ✅ Check FTP port 990 accessible (`telnet 192.168.1.100 990`)
- ✅ Verify G-code file not too large (>100MB may timeout)
- ✅ Increase `ftp.timeout` in config
- ✅ Check printer storage not full

### Print Doesn't Start

**Symptom**: Upload completes but print doesn't start

**Solutions**:
- ✅ Check printer state (may be in error/maintenance mode)
- ✅ Verify G-code file compatible with printer
- ✅ Check printer touchscreen for error messages
- ✅ Try starting print manually from touchscreen to verify file

---

## Next Steps

- ✅ **Integration**: Connect to Job Orchestration (Feature 004)
- ✅ **Scaling**: Add multiple printer support
- ✅ **Monitoring**: Set up alerts for printer offline/errors
- ✅ **Optimization**: Tune retry logic and polling intervals

---

## Resources

- [Bambu Lab Wiki - Third-party Integration](https://wiki.bambulab.com/en/software/third-party-integration)
- [bambulabs_api Documentation](https://github.com/BambuTools/bambulabs_api)
- [LeSign Printer Control API Reference](./contracts/api-contract.md)
- [LeSign Printer Control Spec](./spec.md)
