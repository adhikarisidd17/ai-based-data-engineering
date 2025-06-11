from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .gh_api_handler import create_pr_via_github_api

app = FastAPI()

class Request(BaseModel):
    analyst_prompt: str

@app.post("/requests")
def handle_request(req: Request):
    try:
        pr_url = create_pr_via_github_api(req.analyst_prompt)
    except Exception as e:
        # bubble up errors as 400
        raise HTTPException(status_code=400, detail=str(e))
    return {"pr_url": pr_url}
