# Backend Rules

## Scope

ExamNova backend should remain a narrow control layer:

- route requests
- execute one skill
- return structured output
- persist lightweight local state

## Preferred Structure

- `app/agent`: routing and orchestration
- `app/skills`: learning, thinking, companion
- `app/routes`: HTTP layer only
- `app/schemas`: request/response models
- `app/services`: persistence, clients, adapters

## Constraints

- Do not let route files accumulate business logic.
- Prefer dedicated skill functions over inline response assembly.
- Keep settings persistence local and explicit.
- Add OCR and LLM clients under `services/` or `tools/`, not inside route files.
