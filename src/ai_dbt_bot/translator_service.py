# translator_service.py

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import openai
import requests
load_dotenv()
# Load env: OPENAI_API_KEY, TECHNICAL_SERVICE_URL, TECHNICAL_SERVICE_TOKEN
openai.api_key = os.getenv("OPENAI_API_KEY")
TECH_URL   = os.getenv("TECH_SERVICE_URL")   # e.g. "https://prbot.mycompany.com/requests"
TECH_TOKEN = os.getenv("TECH_SERVICE_TOKEN")

app = FastAPI(title="High-Level Translator")

class HighLevelRequest(BaseModel):
    business_prompt: str
    session_id: str | None = None

@app.post("/translate-and-forward")
def translate_and_forward(req: HighLevelRequest):
    # 1) Ask the LLM to map your high-level ask into a JSON payload
    sys_msg = """
    You are a dbt‐savvy engineer. The user request is:
      \"\"\"{business_prompt}\"\"\"
    Return ONLY a JSON object with two fields:
      - files: a list of dbt model (and schema) file paths this affects
      - prompt: a technical instruction string describing exactly what to change in each file
    Do NOT wrap the JSON in any markdown or text.
    """.format(business_prompt=req.business_prompt)

    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":sys_msg},
            {"role":"user","content":req.business_prompt}
        ],
        temperature=0
    )
    try:
        # Parse the model’s output as JSON
        payload = resp.choices[0].message.content
        data = __import__("json").loads(payload)
        files = data["files"]
        technical_prompt = data["prompt"]
    except Exception as e:
        raise HTTPException(500, f"Failed to parse LLM JSON: {e}\nOutput: {payload}")

    # 2) Forward to PR-Bot
    headers = {
        "Authorization": f"Bearer {TECH_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "session_id": req.session_id,
        "file_names": files,
        "analyst_prompt": technical_prompt
    }
    resp = requests.post(TECH_URL, json=body, headers=headers)
    if not resp.ok:
        raise HTTPException(resp.status_code, resp.text)

    return resp.json()
