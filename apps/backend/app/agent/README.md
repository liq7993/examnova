# Agent

The ExamNova backend uses a single agent.

Responsibilities:

- classify user intent
- pick one skill
- normalize outputs
- expose a single route contract through `/api/agent/run`

The agent should not become a second product layer. It remains a control layer.
