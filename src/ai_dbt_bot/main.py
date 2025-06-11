from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .gh_api_handler import create_pr_for_prompt

app = FastAPI()

class Request(BaseModel):
    analyst_prompt: str

@app.post("/requests")
async def handle_request(req: Request):
    try:
        pr_url = create_pr_for_prompt(req.analyst_prompt)
    except Exception as e:
        detail = f"{type(e).__name__}: {e}"
        raise HTTPException(status_code=400, detail=detail)
    return {"pr_url": pr_url}