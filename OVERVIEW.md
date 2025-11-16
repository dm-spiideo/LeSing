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

**Purpose**: Converts 2D designs into printable 3D models.

**Core Responsibilities**:
- Image to 2D vector conversion
- 2D-to-3D model conversion
- Model optimization and validation
- G-code generation and slicing

**Subcomponents**:
- Model Converter
- Slicer Engine
- Printability Validator

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

**Core Responsibilities**:
- G-code execution on printer hardware
- Print job initiation and control
- Local job buffering

**Subcomponents**:
- Printer Agent
- Hardware Interface
- Local Queue

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
├── frontend/              # Front-end web server and UI
│   ├── web-ui/           # React/Vue design browser and creator
│   ├── api-server/       # Backend API for orders and users
│   └── payment/          # Payment integration module
├── backend/               # Backend processing pipeline
│   ├── ai-generation/    # Diffusion model integration
│   ├── design-library/   # Design storage and management
│   ├── model-converter/  # 2D to 3D conversion service
│   ├── slicer/           # G-code generation service
│   └── queue-manager/    # Print job orchestration
├── printer-agent/         # Local 3D printer integration
│   ├── printer-control/  # Printer communication
│   ├── monitoring/       # Status reporting and cameras
│   └── local-queue/      # Job buffering
├── shared/                # Shared libraries and utilities
│   ├── models/           # Data models and schemas
│   └── protocols/        # Communication protocols
├── infrastructure/        # IaC and deployment configs
│   ├── terraform/        # Cloud infrastructure
│   └── kubernetes/       # Container orchestration
└── docs/                  # Documentation and specifications
```

## Next Steps

Refer to the `investigations/` directory for detailed research, architectural decisions, and implementation planning for each component.
