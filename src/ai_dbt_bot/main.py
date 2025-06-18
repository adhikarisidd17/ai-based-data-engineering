
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .gh_api_handler import create_or_update_pr
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["*"] to permit all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

from .gh_api_handler import repo  # Add this import at the top or before usage

@app.get("/preview/{pr_number}")
def preview_pr(pr_number: int):
    try:
        pr = repo.get_pull(pr_number)
        files = []
        for f in pr.get_files():
            files.append({
                "filename":  f.filename,
                "status":    f.status,
                "additions": f.additions,
                "deletions": f.deletions,
                "patch":     f.patch,       # the unified-diff snippet
            })
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))