---
name: examnova-builder
description: Use this skill when creating or updating the ExamNova desktop app, its FastAPI backend, or its product copy. It preserves ExamNova's Windows-first, single-agent architecture, onboarding flow, calm UI tone, and teaching-mode output constraints.
---

# ExamNova Builder

## Overview

This skill keeps ExamNova coherent while it grows. Use it when editing the desktop UI, backend agent/skill structure, onboarding flow, or product copy so the project stays aligned with its original rules.

## Core Rules

- Keep ExamNova as a `single agent + multiple skills` product.
- Preserve `Windows-first` behavior and documentation.
- Keep the UI restrained, utility-first, and slightly warm rather than pure white.
- Teaching flows must not use emoticons.
- Companion responses may use at most one light emoticon.
- Do not expand the product into multi-agent orchestration unless the user explicitly changes direction.
- Prefer desktop workflows over mobile assumptions.

## When To Use This Skill

Use this skill for requests like:

- "Add a new page or workflow to ExamNova."
- "Refactor the backend agent or skills."
- "Update the onboarding or API setup flow."
- "Improve the product copy without changing the tone."
- "Add OCR, settings persistence, or LLM wiring while keeping the original product shape."

## Working Workflow

1. Read the current files being changed and identify whether the task affects `desktop`, `backend`, or both.
2. Preserve the product boundary:
   - `desktop` handles onboarding, interaction, and rendering
   - `backend` handles agent routing, skill execution, and storage
3. If adding logic, prefer extending an existing skill module before adding a new abstraction layer.
4. If changing copy, keep the voice calm, concise, and non-performative.
5. If adding UX, protect the first-run flow:
   - splash
   - welcome
   - feature intro
   - API setup
   - workspace

## Backend Guidance

- Keep the backend organized around:
  - `app/agent`
  - `app/skills`
  - `app/routes`
  - `app/schemas`
  - `app/services`
- Prefer structured schemas over free-form dictionaries.
- Prefer deterministic skill functions until real OCR/LLM integrations are wired.
- When the task needs architecture context, read [`references/backend-rules.md`](references/backend-rules.md).

## Frontend Guidance

- Keep the UI clean and legible on Windows.
- Prefer focused panels and simple actions over dashboard clutter.
- Preserve the off-white palette and restrained visual language.
- Do not introduce playful visual elements into teaching surfaces.
- When the task needs product/UI context, read [`references/ui-rules.md`](references/ui-rules.md).
