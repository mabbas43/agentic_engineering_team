"""The agents' hands: read, write and run code inside a disposable sandbox.

Nothing the agents write ever executes on the host. `run_sandbox_python` starts a
throwaway Docker container with only the sandbox directory mounted, so the worst a
confused agent can do is break its own workspace.
"""

import os
import shutil
import subprocess
from pathlib import Path

from crewai.tools import tool

SANDBOX_DIR = Path(__file__).parents[3] / "sandbox"
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
IMAGE = os.getenv("SANDBOX_IMAGE", "ghcr.io/astral-sh/uv:python3.12-bookworm-slim")
TIMEOUT = int(os.getenv("SANDBOX_TIMEOUT", "300"))


def _resolve(filename: str) -> Path | None:
    """Resolve a filename inside the sandbox, refusing anything that escapes it."""
    path = (SANDBOX_DIR / filename).resolve()
    if path.parent != SANDBOX_DIR.resolve():
        return None
    return path


def reset_sandbox() -> None:
    """Wipe the sandbox and set it up as a fresh uv project with gradio available."""
    if SANDBOX_DIR.exists():
        shutil.rmtree(SANDBOX_DIR)
    SANDBOX_DIR.mkdir(parents=True)
    subprocess.run(["uv", "init", "--bare", "--python", "3.12"], cwd=SANDBOX_DIR, check=True)
    subprocess.run(["uv", "add", "gradio"], cwd=SANDBOX_DIR, check=True)


@tool("List Sandbox Files")
def list_sandbox_files() -> str:
    """List the files currently in the sandbox directory.

    Returns:
        A newline-separated list of filenames.
    """
    names = sorted(p.name for p in SANDBOX_DIR.iterdir() if not p.name.startswith("."))
    return "\n".join(names) if names else "The sandbox is empty."


@tool("Read Sandbox File")
def read_sandbox_file(filename: str) -> str:
    """Read a file from the sandbox directory.

    Args:
        filename: Name of the file, e.g. "backend.py".
    Returns:
        The file's contents.
    """
    path = _resolve(filename)
    if path is None:
        return "Refused: files must live directly in the sandbox directory."
    if not path.is_file():
        return f"No such file in the sandbox: {filename}"
    return path.read_text()


@tool("Write Sandbox File")
def write_sandbox_file(filename: str, content: str) -> str:
    """Write a file into the sandbox directory, replacing anything already there.

    Args:
        filename: Name of the file, e.g. "backend.py".
        content: The full text to write.
    Returns:
        A confirmation message.
    """
    path = _resolve(filename)
    if path is None:
        return "Refused: files must live directly in the sandbox directory."
    path.write_text(content)
    return f"Wrote {len(content)} characters to {filename}."


@tool("Run Sandbox Python File")
def run_sandbox_python(filename: str) -> str:
    """Run a Python file from the sandbox inside a disposable Docker container.

    Args:
        filename: Name of the file to run, e.g. "test_backend.py".
    Returns:
        The script's output, including any error it printed.
    """
    path = _resolve(filename)
    if path is None or not path.is_file():
        return f"No such file in the sandbox: {filename}"

    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                # Run as the host user. Without this the container writes
                # root-owned files into the mounted sandbox, and the next
                # reset_sandbox() can't delete them.
                "--user", f"{os.getuid()}:{os.getgid()}",
                "-e", "HOME=/tmp",
                "-e", "UV_CACHE_DIR=/tmp/uv-cache",
                "-v", f"{SANDBOX_DIR}:/workspace",
                "-w", "/workspace",
                IMAGE,
                "uv", "run", filename,
            ],
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return f"Timed out after {TIMEOUT}s. Does the script block, or call .launch()?"
    except FileNotFoundError:
        return "Docker isn't available on this machine — the sandbox can't run code."

    # Tests report failures on stderr, so returning stdout alone would let a
    # failing test suite look like a passing one.
    return (
        f"exit code: {result.returncode}\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- stderr ---\n{result.stderr}"
    )


sandbox_tools = [list_sandbox_files, read_sandbox_file, write_sandbox_file, run_sandbox_python]


def _never_cache(*_args, **_kwargs) -> bool:
    return False


# The sandbox changes between calls — files get written, code gets fixed. Cached
# tool results would feed agents a stale view of their own workspace.
for _tool in sandbox_tools:
    _tool.cache_function = _never_cache
