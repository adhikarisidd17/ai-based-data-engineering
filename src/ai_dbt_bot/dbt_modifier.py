import subprocess
from pathlib import Path
from typing import Tuple

def apply_patch(repo_path: Path, diff_text: str) -> Tuple[bool, str]:
    """
    Applies a unified diff to the git repo.
    Returns (success, output).
    """
    p = subprocess.run(
        ["git", "apply", "--unidiff-zero", "-"],
        cwd=repo_path,
        input=diff_text.encode(),
        capture_output=True,
    )
    return (p.returncode == 0, p.stderr.decode() or p.stdout.decode())
