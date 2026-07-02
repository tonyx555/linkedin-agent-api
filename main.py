import subprocess
import json
import os
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Cookie-based auth — no browser/display needed
LI_AT = os.environ.get("LINKEDIN_LI_AT")
JSESSIONID = os.environ.get("LINKEDIN_JSESSIONID")

def run_cli(args: list) -> dict:
    env = {
        **os.environ,
        "LINKEDIN_LI_AT": LI_AT,
        "LINKEDIN_JSESSIONID": JSESSIONID
    }
    result = subprocess.run(
        ["linkedin"] + args + ["--json"],
        capture_output=True, text=True, env=env
    )
    try:
        return json.loads(result.stdout)
    except:
        return {"error": result.stderr or result.stdout}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/search")
def search(req: SearchRequest):
    return run_cli(["search", "people", 
                    "--keywords", req.query])

class SearchRequest(BaseModel):
    query: str

class ConnectRequest(BaseModel):
    profileId: str
    message: str

@app.post("/connect")
def connect(req: ConnectRequest):
    return run_cli(["connections", "add", 
                    req.profileId, "-m", req.message])

@app.post("/message")
def message(req: ConnectRequest):
    return run_cli(["messaging", "send",
                    req.profileId, req.message])

@app.get("/inbox")
def inbox():
    return run_cli(["messaging", "conversations"])
