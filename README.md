# ExamNova

ExamNova is a Windows-first AI study workbench for exam-focused review.  
It is designed around a structured note workflow instead of a generic chat interface.

面向中国大学生的桌面复习工作台。  
定位偏向考试前冲刺、短期强化记忆与结构化题解。

## Overview

ExamNova does not aim to be a general-purpose chatbot.  
It focuses on a narrower workflow:

- read a problem
- generate a structured explanation
- turn the result into a Cornell-style long note
- keep review prompts and study state running quietly in the background
- continue the same course in thread-based workspaces

Current product lines:

- `learning`: problem analysis, explanation, solution steps, review prompts, wrongbook flow
- `thinking`: reflection notes, writing drafts, recap, and next actions

## Highlights

- `single-agent + domain templates + local services`
- Cornell-style long-page study notes instead of fragmented cards
- Thread-based study workspace for different courses
- Formula rendering embedded across explanations and solution steps
- Local-first Electron + FastAPI desktop architecture
- Exam-focused review logic with cram and standard modes

## Current Scope

The current version is strongest on structured STEM workflows, especially problem-solving oriented tasks.  
Recent stability work has focused on engineering and mechanical-style problem templates rather than broad multi-discipline coverage.

This means the project is intentionally stronger at:

- structured problem explanation
- formula-based solution flow
- short-cycle review before exams
- local desktop usage and demoability

It is not yet positioned as:

- a universal academic tutor for all subjects
- a high-accuracy handwriting OCR system
- a fully autonomous multi-agent platform

## Architecture

ExamNova follows a `single-agent + skill modules + service layer` structure.

- Agent layer: unified task routing and result normalization
- Skill layer: learning and writing/recap capabilities
- Service layer: OCR, LLM integration, study state, review strategy, storage

Main implementation areas:

- `apps/backend`: FastAPI backend, routing, schemas, storage, review logic
- `apps/desktop`: Next.js + React UI and Electron desktop shell
- `docs`: architecture, packaging, setup, GitHub showcase notes
- `scripts`: startup, stop, model setup, and packaging helpers

Detailed architecture notes:

- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)

## Repository Structure

```text
examnova/
├── apps/
│   ├── backend/
│   └── desktop/
├── codex-skills/
├── docs/
├── packages/
├── scripts/
├── .env.example
├── examnova.txt
└── README.md
```

## Local Data and Open-Source Safety

The repository is intended to stay safe for open-source publication.  
Runtime data is stored outside tracked source files.

Default locations:

```text
Development: <repo>/.examnova-data
Desktop build: <ExamNova executable directory>/data
```

These runtime folders may contain:

- `settings.json`
- `examnova.db`
- optional JSONL migration files
- Electron local cache and thread state

Ignored from git:

- `.examnova-data/`
- `apps/desktop/release/`
- `apps/backend-dist/`

## Getting Started

### Backend

```powershell
cd apps/backend
python -m pip install -e .
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend

```powershell
cd apps/desktop
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

### Script-based startup

```powershell
cd <repo-root>
.\scripts\start-backend.ps1
.\scripts\start-desktop.ps1
.\scripts\start-all.ps1
```

## Packaging

ExamNova currently uses an `Electron + FastAPI` packaging route.

- Desktop shell: `apps/desktop/electron/`
- Backend entry: `apps/backend/run_backend.py`
- Packaging script: `scripts/package-electron.ps1`

Build command:

```powershell
cd <repo-root>
.\scripts\package-electron.ps1
```

More details:

- [docs/PACKAGING.md](./docs/PACKAGING.md)

## MiniMax Integration

MiniMax setup notes:

- [docs/MINIMAX.md](./docs/MINIMAX.md)
- [docs/MINIMAX-BEGINNER.txt](./docs/MINIMAX-BEGINNER.txt)

The project also supports a demo mode, so the UI and workflow can be explored without external model calls.

## GitHub Showcase

For repository presentation and screenshot planning:

- [docs/GITHUB-SHOWCASE.md](./docs/GITHUB-SHOWCASE.md)
- [docs/screenshots/README.md](./docs/screenshots/README.md)

## Product Principles

- one page, one reading flow
- focus on question, explanation, and recap
- confidence without motivational fluff
- local-first and explainable before feature sprawl
- exam-oriented short-cycle review over noisy general assistance

## Status

This is an actively iterated project aimed at being:

- runnable
- explainable
- demoable
- suitable for open-source presentation

The current codebase is already usable as a portfolio project and desktop demo, while still leaving room for further template coverage, OCR improvements, and UI polish.
