# in src/ai_dbt_bot/dbt_modifier.py
from pathlib import Path
import subprocess
from typing import Tuple

def apply_patch(repo_path: Path, diff_text: str) -> Tuple[bool, str]:
    # DEBUG: dump the patch
    debug_file = repo_path / "last_diff.patch"
    debug_file.write_text(diff_text)

    # try a dry-run check first
    check = subprocess.run(
        ["git", "apply", "--check", "-"],
        cwd=repo_path,
        input=diff_text.encode(),
        capture_output=True,
    )
    if check.returncode != 0:
        return False, check.stderr.decode()

    # actually apply
    p = subprocess.run(
        ["git", "apply", "--unidiff-zero", "-"],
        cwd=repo_path,
        input=diff_text.encode(),
        capture_output=True,
    )
    return (p.returncode == 0, p.stderr.decode() or p.stdout.decode())
