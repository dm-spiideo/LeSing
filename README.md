

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

**Phase**: POC Development
**Active Features**:
- 001-ai-image-generation (✅ Completed)
- 002-3d-model-pipeline (🚧 In Development)

Currently implementing the 3D Model Pipeline that converts AI-generated 2D images into printable 3D models and G-code for the Bambu Lab H2D printer.

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
- **AI Image Generation** - Text-to-image using DALL-E 3 API ✅ Implemented
- **Design Library** - Design storage and management (Planned)
- **3D Model Pipeline** - Image → Vector → 3D → G-code conversion 🚧 In Development
  - model-converter: VTracer + Build123d + Manifold3D
  - slicer: PrusaSlicer CLI wrapper
  - shared: Common utilities and models
- **Job Orchestration** - Print queue and workflow coordination (Planned)

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
├── backend/
│   ├── ai-generation/      # DALL-E 3 image generation (Python 3.11+)
│   ├── model-converter/    # Image→Vector→3D conversion (Python 3.12)
│   ├── slicer/            # 3D→G-code generation (Python 3.12)
│   └── shared/            # Shared utilities
├── specs/                 # Feature specifications
├── investigations/        # Research artifacts
└── .github/              # CI/CD workflows
```

## Getting Started

### For Developers

**AI Image Generation**:
- See [backend/ai-generation/README.md](backend/ai-generation/README.md)
- Python 3.11+ with OpenAI API integration
- 95 tests, 91% coverage

**3D Model Pipeline**:
- See [specs/002-3d-model-pipeline/quickstart.md](specs/002-3d-model-pipeline/quickstart.md)
- Python 3.12 with VTracer, Build123d, PrusaSlicer CLI
- TDD approach with >90% coverage target

### Documentation

- [OVERVIEW.md](OVERVIEW.md) - Project architecture and components
- [PLAN.md](PLAN.md) - Component implementation tracking
- [specs/](specs/) - Feature specifications
- [Constitution](.specify/memory/constitution.md) - Development principles
