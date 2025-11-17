# LeSign Project Overview

## Project Description

LeSign is a fully automated name sign manufacturing platform that transforms text prompts into physical 3D-printed name signs with zero manual intervention. Users simply provide a text description or select from a library of existing designs, and the system automatically handles everything else: AI image generation, 3D model creation, and physical printing.

**User Journey**: Text Prompt → AI-Generated Design → Automated 3D Conversion → Order → Physical Product Printed & Shipped


## Component Overview

1. **Web Interface** - User-facing design creation and browsing
2. **Payment Processing** - Transaction handling and order management
3. **AI Image Generation** - Text-to-image generation using diffusion models
4. **Design Library** - Storage and retrieval of existing designs
5. **3D Model Pipeline** - Automated Image → 2D → 3D conversion and optimization
6. **Job Orchestration** - Print queue management and workflow coordination
7. **Printer Control** - Direct communication with 3D printer hardware
8. **Status Monitoring** - Real-time tracking of printer and job status

## Core Components

### 1. Web Interface

**Purpose**: User-facing application for design creation and order placement.

**Core Responsibilities**:
- Text prompt input for custom designs
- Design preview and approval
- User account and order history

**Subcomponents**:
- Design Browser
- Prompt Interface
- Order Dashboard

---

### 2. Payment Processing

**Purpose**: Handles all financial transactions and order confirmation.

**Core Responsibilities**:
- Payment transaction processing
- Order confirmation and receipt generation
- Payment status tracking

---

### 3. Design Library

**Purpose**: Manages storage and retrieval of design assets.

**Core Responsibilities**:
- Design storage and indexing
- Search and filtering capabilities
- Design versioning and metadata

---

### 4. Image Generation

**Purpose**: Converts text prompts into 2D design images.

**Core Responsibilities**:
- Text-to-image generation using diffusion models
- Design quality validation
- Image output optimization

---

### 5. 3D Model Pipeline

**Purpose**: Converts AI-generated 2D images into printable 3D models and G-code.

**Status**: 🚧 In Development (Feature 002)

**Core Responsibilities**:
- Image to SVG vector conversion using VTracer
- SVG to 3D extrusion using Build123d CAD library
- Mesh validation and repair (watertight, manifold)
- Quality metrics validation (SSIM ≥0.85, Edge IoU ≥0.75)
- G-code generation with PrusaSlicer CLI
- Bambu Lab H2D printer profile support

**Technologies**:
- Python 3.12, VTracer, Build123d, trimesh, Manifold3D, PrusaSlicer CLI, scikit-image, opencv-python

**Subcomponents**:
- **model-converter**: Image→Vector→3D conversion with quality validation
- **slicer**: 3D→G-code generation with printer profiles
- **shared**: Common utilities, models, and error handling

**File Outputs**:
- SVG files (≤8 colors, <5MB, <1000 paths)
- 3MF files (watertight, manifold, ≤256mm build volume)
- G-code files (Bambu Lab H2D compatible)

---

### 6. Job Orchestration

**Purpose**: Manages the end-to-end workflow from order to completion.

**Core Responsibilities**:
- Print queue management
- Printer selection and job routing
- Workflow state coordination

**Subcomponents**:
- Queue Manager
- Workflow Engine
- Status Tracker

---

### 7. Printer Control

**Purpose**: Direct communication and control of 3D printer hardware.

**Status**: 🚧 In Development (Feature 003)

**Core Responsibilities**:
- G-code execution on printer hardware via FTP upload
- Print job initiation and control via MQTT
- Local job buffering with persistent queue
- Real-time status monitoring

**Technologies**:
- Python 3.12, bambulabs-api, paho-mqtt, tenacity, structlog

**Subcomponents**:
- Printer Agent: Job orchestration and queue management
- Printer Interface: MQTT/FTP communication with Bambu Lab H2D
- Local Queue: Persistent job queue with retry logic

---

### 8. Status Monitoring

**Purpose**: Tracks printer status and job progress.

**Core Responsibilities**:
- Printer availability tracking
- Print progress monitoring
- Error detection and reporting

**Subcomponents**:
- Health Monitor
- Progress Tracker
- Alert System

---

## System Architecture

```
┌────────────────────────────────────────────┐
│              User Layer                    │
│  ┌──────────────┐    ┌──────────────────┐  │
│  │     Web      │    │     Payment      │  │
│  │  Interface   │    │   Processing     │  │
│  └──────────────┘    └──────────────────┘  │
└────────────────────────┬───────────────────┘
                         │
┌────────────────────────┼────────────────────┐
│                        ▼                    │
│             Processing Layer                │
│  ┌──────────────┐    ┌──────────────────┐   │
│  │  AI Image    │    │    Design        │   │
│  │  Generation  │    │    Library       │   │
│  └──────────────┘    └──────────────────┘   │
│                                             │
│  ┌──────────────┐    ┌──────────────────┐   │
│  │  3D Model    │    │      Job         │   │
│  │   Pipeline   │    │  Orchestration   │   │
│  └──────────────┘    └──────────────────┘   │
└────────────────────────┬────────────────────┘
                         │
┌────────────────────────┼────────────────────┐
│                        ▼                    │
│             Hardware Layer                  │
│  ┌──────────────┐    ┌──────────────────┐   │
│  │   Printer    │    │     Status       │   │
│  │   Control    │    │   Monitoring     │   │
│  └──────────────┘    └──────────────────┘   │
└─────────────────────────────────────────────┘
```

## Architectural Philosophy

### Modular Component Structure for End-to-End Automation

The core principle driving LeSign's architecture is **complete automation** achieved through **highly modular, independent components**. Each component in the system is designed as a self-contained unit with:

- **Clear Input/Output Contracts**: Well-defined interfaces that enable seamless component chaining
- **Independent Operation**: Each module can be developed, tested, deployed, and scaled independently
- **Automation-First Design**: Components are built to operate without human intervention
- **Composability**: Modules can be orchestrated into automated pipelines

This modular approach enables:
1. **Parallel Development**: Teams can work on different components simultaneously
2. **Easy Testing**: Individual components can be tested in isolation and integration
3. **Flexible Scaling**: Scale specific bottleneck components (e.g., AI generation) independently
4. **Rapid Iteration**: Replace or upgrade components without affecting the entire system
5. **End-to-End Automation**: Chain components together to create fully automated workflows

**Example Pipeline Flow**:
```
Design Input → [AI Generator] → Image → [3D Converter] → Model →
[Slicer] → G-code → [Queue Manager] → [Printer Agent] → Physical Product
```

Each bracketed component is a standalone module with its own:
- Input validation
- Processing logic
- Error handling
- Output verification
- Status reporting

## Design Principles

### Automation
- Zero manual intervention from order to completion
- Self-healing with automatic error recovery
- Event-driven component coordination

### Modularity
- Independent, composable components
- Clear interface contracts between modules
- Individual component scalability

### Reliability
- Fault tolerance at all layers
- Graceful degradation on failures
- Offline operation capability for hardware

### Security
- End-to-end data encryption
- Secure payment processing
- Component authentication and authorization

## Repository Structure

```
lesign/
├── backend/                  # Backend processing pipeline
│   ├── ai-generation/       # DALL-E 3 image generation (Feature 001) ✅
│   │   ├── src/            # Source code
│   │   ├── tests/          # Test suite (95 tests, 91% coverage)
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   ├── model-converter/     # Image→Vector→3D conversion (Feature 002) ✅
│   │   ├── src/            # Converter, vectorizer, validator, repairer
│   │   ├── tests/          # Contract, integration, unit tests
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   ├── slicer/             # 3D→G-code generation (Feature 002) ✅
│   │   ├── src/            # PrusaSlicer CLI wrapper
│   │   ├── tests/          # Slicing tests
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   ├── shared/             # Shared utilities (Feature 002) ✅
│   │   ├── models.py       # Pydantic models
│   │   ├── exceptions.py   # Error hierarchy
│   │   └── logging_config.py
│   └── printer-control/    # Bambu Lab printer control (Feature 003) 🚧
│       ├── src/printer_control/  # Agent, printer, queue, models
│       ├── tests/          # Unit, integration, contract tests
│       ├── config/         # Printer profiles
│       ├── requirements.txt
│       └── pyproject.toml
├── specs/                   # Feature specifications
│   ├── 001-ai-image-generation/
│   ├── 002-3d-model-pipeline/
│   └── 003-printer-control/
├── investigations/          # Research artifacts
├── .github/workflows/       # CI/CD pipelines
└── .specify/               # Project constitution and templates
```

## Next Steps

Refer to the `investigations/` directory for detailed research, architectural decisions, and implementation planning for each component.
