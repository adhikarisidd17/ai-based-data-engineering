from git import Repo
from pathlib import Path
import uuid
from .dbt_modifier import apply_patch

def create_branch_and_commit(repo_path: Path, diff_text: str, analyst_request: str) -> str:
    repo = Repo(repo_path)
    branch_name = f"feature/add-kpi-{uuid.uuid4().hex[:8]}"
    repo.git.checkout("origin/main", b=branch_name)
    success, out = apply_patch(repo_path, diff_text)
    if not success:
        raise RuntimeError(f"Patch failed: {out}")
    repo.git.add(all=True)
    repo.git.commit(m=f"chore: add KPI per analyst request – {analyst_request}")
    repo.git.push("--set-upstream", "origin", branch_name)
    return branch_name
