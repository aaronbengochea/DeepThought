# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DeepThought is a Claude agent framework for building AI-powered applications. It uses a three-part architecture: a FastAPI backend, a frontend (TBD), and an agent orchestration layer.

## Current State

This project is in early scaffolding phase. Most files contain only placeholder comments or headings. There are no dependencies configured yet (no requirements.txt or pyproject.toml).

## Architecture

```
DeepThought/
├── agent/           # Claude agent templates and orchestration
│   ├── backend.md   # Backend agent template
│   ├── frontend.md  # Frontend agent template
│   └── skills.md    # Skills/capabilities for agent orchestration
├── backend/         # Python FastAPI server
│   └── server.py    # API routes (placeholder)
└── frontend/        # Frontend client (not yet implemented)
```

## Technology Stack

- **Backend**: Python with FastAPI
- **Frontend**: To be determined
- **Agent System**: Claude integration via agent templates

## Development Commands

Once dependencies are established:

```bash
# Backend (FastAPI)
pip install -r requirements.txt          # Install dependencies (when created)
uvicorn backend.server:app --reload      # Run development server
```

## Next Steps for Implementation

1. Create `requirements.txt` with FastAPI and dependencies
2. Implement actual FastAPI routes in `backend/server.py`
3. Define agent orchestration patterns in `agent/` templates
4. Build frontend
