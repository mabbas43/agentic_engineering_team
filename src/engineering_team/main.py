#!/usr/bin/env python
import json
import sys
import warnings
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

from engineering_team.crew import EngineeringTeam  # noqa: E402
from engineering_team.tools.sandbox_tools import SANDBOX_DIR, reset_sandbox  # noqa: E402

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

REQUIREMENTS_FILE = Path(__file__).parents[2] / "requirements.md"


def _load_requirements(path: str | None = None) -> str:
    source = Path(path) if path else REQUIREMENTS_FILE
    if not source.is_file():
        raise SystemExit(f"No requirements file at {source}")
    return source.read_text()


def run() -> None:
    """Build whatever requirements.md describes. Pass a path to use a different file."""
    requirements = _load_requirements(sys.argv[1] if len(sys.argv) > 1 else None)

    print("Building from the requirements. The sandbox will be wiped first.\n")
    reset_sandbox()
    EngineeringTeam().crew().kickoff(inputs={"requirements": requirements})
    print(f"\nDone. The team's work is in {SANDBOX_DIR}")
    print("Run the app with:  cd sandbox && uv run app.py")


def train() -> None:
    """Train the crew. Usage: train <n_iterations> <filename.pkl>"""
    if len(sys.argv) < 3:
        raise SystemExit("Usage: train <n_iterations> <filename.pkl>")
    reset_sandbox()
    EngineeringTeam().crew().train(
        n_iterations=int(sys.argv[1]),
        filename=sys.argv[2],
        inputs={"requirements": _load_requirements()},
    )


def replay() -> None:
    """Replay the last run from a given task. Usage: replay <task_id>"""
    if len(sys.argv) < 2:
        raise SystemExit("Usage: replay <task_id>  (find ids with `crewai log-tasks-outputs`)")
    EngineeringTeam().crew().replay(task_id=sys.argv[1])


def test() -> None:
    """Evaluate the crew. Usage: test <n_iterations> <eval_llm>"""
    if len(sys.argv) < 3:
        raise SystemExit("Usage: test <n_iterations> <eval_llm>")
    reset_sandbox()
    EngineeringTeam().crew().test(
        n_iterations=int(sys.argv[1]),
        eval_llm=sys.argv[2],
        inputs={"requirements": _load_requirements()},
    )


def run_with_trigger():
    """Run with a JSON trigger payload whose "requirements" key replaces requirements.md."""
    if len(sys.argv) < 2:
        raise SystemExit("No trigger payload provided. Pass a JSON payload as the argument.")
    try:
        payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise SystemExit("Invalid JSON payload provided as argument")

    reset_sandbox()
    return EngineeringTeam().crew().kickoff(
        inputs={
            "crewai_trigger_payload": payload,
            "requirements": payload.get("requirements") or _load_requirements(),
        }
    )


if __name__ == "__main__":
    run()
