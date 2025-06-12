from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from .translator_service import app as translator_app
from .gh_api_handler import create_or_update_pr

app = FastAPI()
app.mount("/translate-and-forward", translator_app)

class Request(BaseModel):
    session_id: str | None = None  # unique identifier for the user session or conversation
    analyst_prompt: str

@app.post("/requests")
async def handle_request(req: Request):
    try:
        result = create_or_update_pr(req.session_id, req.analyst_prompt)
    except Exception as e:
        detail = f"{type(e).__name__}: {e}"
        raise HTTPException(status_code=400, detail=detail)
    return {"message": result}