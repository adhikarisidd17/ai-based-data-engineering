import ssl
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path

from .llm_engine import generate_dbt_patch
from .git_handler import create_branch_and_commit
from .pr_handler import open_pr
ssl._create_default_https_context = ssl._create_unverified_context
app = FastAPI()
REPO_PATH = Path.cwd()

class Request(BaseModel):
    analyst_prompt: str

@app.post("/requests")
def handle_request(req: Request):
    # 1. Generate patch
    diff = generate_dbt_patch(req.analyst_prompt)
    # 2. Create branch & commit
    try:
        branch = create_branch_and_commit(REPO_PATH, diff, req.analyst_prompt)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    # 3. Open PR
    pr_url = open_pr(
        branch=branch,
        title=f"Add KPI: {req.analyst_prompt[:50]}…",
        body=(
            f"Automated PR to add KPI per analyst request:\n\n"
            f"> {req.analyst_prompt}\n\n"
            "Please review and merge."
        )
    )
    return {"pr_url": pr_url}
