
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .gh_api_handler import create_or_update_pr

app = FastAPI()

class Request(BaseModel):
    session_id: str | None = None
    file_names: list[str] | None = None      # <— new!
    analyst_prompt: str

@app.post("/requests")
async def handle_request(req: Request):
    try:
        result = create_or_update_pr(
            session_id    = req.session_id,
            analyst_prompt= req.analyst_prompt,
            file_names    = req.file_names   # pass it through
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": result, "session_id": req.session_id}