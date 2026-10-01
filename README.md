# Project 5 — Engineering Team

Four agents that take a paragraph of requirements and hand you back a working application:
a lead designs it, a backend engineer builds it, a frontend engineer wraps it in a Gradio
UI, and a test engineer writes tests and fixes the code until they pass.

Every line of code they write runs **inside a Docker container**, never on your machine.

## How it works

```
requirements.md
      │
      ▼
 Engineering lead ──▶ design.md          (Context7 docs only — design, no code)
      │
      ▼
 Backend engineer ──▶ backend module     ┐
      │                                  │
      ▼                                  ├─ all four sandbox tools:
 Frontend engineer ─▶ app.py             │   list / read / write / run
      │                                  │
      ▼                                  ┘
 Test engineer ────▶ tests, and fixes until they pass
                          │
                          ▼
                   ┌─────────────┐
                   │  sandbox/   │──mounted──▶ docker run --rm  ──▶ output
                   └─────────────┘             (disposable, no network need)
```

**The sandbox is the whole idea.** Agents that write code are only useful if they can run
it, and code written by a language model is exactly the code you don't want executing on
your laptop. `run_sandbox_python` starts a throwaway container with nothing mounted but the
sandbox directory. The worst a confused agent can do is break its own workspace, and
`--rm` deletes the container either way.

**The lead has no sandbox tools, deliberately.** Give an agent the ability to write files
and it will write the implementation instead of designing it. Removing those tools is what
keeps the design a design.

**The lead and frontend engineer can read current docs.** Both are connected to the
[Context7](https://context7.com) MCP server, so they check the real Gradio 6 API instead of
recalling an older one from training data. The lead writes "Gradio 6 notes" into the design
for the frontend engineer to follow.

**The test engineer is the only agent with a real loop.** It runs tests, reads the failure,
edits the backend, runs again — up to `max_iter=30`. That loop is why the output usually
works rather than merely looking plausible.

- `requirements.md` — what to build. This is the file you edit.
- `config/agents.yaml` / `config/tasks.yaml` — the team and their instructions
- `tools/sandbox_tools.py` — the four tools and the Docker call
- `crew.py` — wiring, models, iteration budgets, MCP servers

## Setup

```bash
cp .env.example .env      # add OPENAI_API_KEY
uv sync
docker --version          # Docker must be running
```

Docker is genuinely required — without it `run_sandbox_python` returns an error and the
engineers fly blind.

Two models are configured separately. `LEAD_MODEL` defaults to a stronger model than
`ENGINEER_MODEL`, because every other agent works from the lead's design: a vague design
wastes three agents' worth of tokens downstream.

## Run it

```bash
uv run run_crew                        # builds what requirements.md describes
uv run run_crew my_other_spec.md       # or point it at any other file
```

The other CrewAI entry points work too: `uv run train <n> <file.pkl>`,
`uv run test <n> <eval_model>`, `uv run replay <task_id>` and
`uv run run_with_trigger '{"requirements": "..."}'`.

**The sandbox is wiped at the start of every run.** Anything you want to keep, copy out first.

A run takes 5-15 minutes. When it finishes:

```bash
cd sandbox
uv run app.py            # the app your agents built
```

The `sandbox/` directory will hold `design.md`, the backend module, `app.py`, a test file,
and `test_summary.md`.

## Writing good requirements

This is the highest-leverage thing you control. The default `requirements.md` works well
because it states the rules the system must *enforce* ("prevent a withdrawal that would
leave a negative balance"), not just the features it has. Those constraints become the
edge-case tests. Requirements written as a feature list produce code that handles only the
happy path.

Keep the scope to something one person could build in an afternoon. This crew builds a
module and a UI, not a system.

## When it goes wrong

- **The app won't start.** Check `test_summary.md` first — the test engineer sometimes fixes
  a backend interface that `app.py` was relying on. The task instructions warn it against
  this, but a smaller model still does it occasionally.
- **A tool call times out.** Almost always `.launch()` in a validation script. It blocks
  forever by design.
- **The agent claims success without running anything.** Raise `ENGINEER_MODEL`. Smaller
  models skip verification steps under instruction pressure.

## Make it yours

- Point it at your own `requirements.md` — this is the fastest way to feel where it breaks.
- Add a `run_shell` sandbox tool so the engineers can install their own dependencies.
- Add a fifth agent — a reviewer that reads the diff before the tests run.
- Swap `SANDBOX_IMAGE` for an image with your stack preinstalled and build something
  other than a Gradio app.
