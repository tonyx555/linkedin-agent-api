import subprocess
import json
import os
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

LINKEDIN_EMAIL = os.environ.get("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.environ.get("LINKEDIN_PASSWORD")

def run_cli(args: list) -> dict:
    result = subprocess.run(
        ["linkedin-cli"] + args,
        capture_output=True, text=True
    )
    try:
        return json.loads(result.stdout)
    except:
        return {"error": result.stderr or result.stdout}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/session/open")
def open_session():
    return run_cli([
        "session", "open",
        "--email", LINKEDIN_EMAIL,
        "--password", LINKEDIN_PASSWORD,
        "--session", "main"
    ])

class SearchRequest(BaseModel):
    query: str

@app.post("/search")
def search(req: SearchRequest):
    return run_cli([
        "search", req.query,
        "--session", "main",
        "--json"
    ])

class ConnectRequest(BaseModel):
    profileId: str
    message: str

@app.post("/connect")
def connect(req: ConnectRequest):
    return run_cli([
        "connect", req.profileId,
        "--message", req.message,
        "--session", "main",
        "--json"
    ])

@app.get("/inbox")
def inbox():
    return run_cli([
        "inbox",
        "--session", "main",
        "--json"
    ])
