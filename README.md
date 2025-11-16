

```
╦  ┌─┐╔═╗┬┌─┐┌┐┌
║  ├┤ ╚═╗││ ┬│││
╩═╝└─┘╚═╝┴└─┘┘└┘
```

Fully automated name sign manufacturing platform that transforms text prompts into physical 3D-printed name signs with zero manual intervention.

</div>

## User Journey

**Text Prompt → AI-Generated Design → Automated 3D Conversion → Order → Physical Product Printed & Shipped**

Users simply provide a text description or select from a library of existing designs. The system automatically handles everything: AI image generation, 3D model creation, and physical printing.

## Current Status

**Phase**: Planning & POC Development
**Milestone**: [POC: End-to-End Pipeline](https://github.com/dm-spiideo/LeSing/milestone/1)

Currently implementing proof-of-concept for the complete pipeline: text prompt → image generation → 2D conversion → simple 3D model → physical print.

## Documentation

- **[OVERVIEW.md](OVERVIEW.md)** - Project architecture, components, and design principles
- **[PLAN.md](PLAN.md)** - High-level implementation tracking and component status
- **[Constitution](.specify/memory/constitution.md)** - Core development principles and governance

## Architecture

LeSign is built on **modular, independent components** organized in three layers:

### User Layer
- Web Interface - Design creation and browsing
- Payment Processing - Transaction handling

### Processing Layer
- AI Image Generation - Text-to-image using diffusion models
- Design Library - Design storage and management
- 3D Model Pipeline - Image → 2D → 3D → G-code conversion
- Job Orchestration - Print queue and workflow coordination

### Hardware Layer
- Printer Control - Direct 3D printer communication
- Status Monitoring - Real-time tracking and alerts

## Core Principles

1. **Modular Components** - Self-contained, independently testable, composable
2. **Test-Driven Development** - Write tests first, 80% minimum coverage
3. **Clear Interfaces** - Explicit contracts between components
4. **Local-First POC** - Validate concepts locally before cloud deployment
5. **Python & Best Practices** - Consistent standards across backend components

See [Constitution](.specify/memory/constitution.md) for detailed principles and governance.

## Repository Structure

```
lesign/
├── frontend/           # Web UI and payment integration
├── backend/            # Processing pipeline (AI, 3D conversion, queue)
├── printer-agent/      # Local 3D printer integration
├── shared/             # Shared libraries and utilities
├── infrastructure/     # IaC and deployment configs
└── docs/              # Documentation and specifications
```

## Getting Started

Currently in planning phase. See [all issues](https://github.com/dm-spiideo/LeSing/issues) or track progress on the [POC milestone](https://github.com/dm-spiideo/LeSing/milestone/1).
