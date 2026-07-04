import requests
import os
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

LI_AT = os.environ.get("LINKEDIN_LI_AT", "")
JSESSIONID = os.environ.get("LINKEDIN_JSESSIONID", "")
EXA_KEY = os.environ.get("EXA_API_KEY", "")

def voyager_get(path: str) -> dict:
    headers = {
        "cookie": f"li_at={LI_AT}; JSESSIONID={JSESSIONID}",
        "csrf-token": JSESSIONID.strip('"'),
        "x-restli-protocol-version": "2.0.0",
        "x-li-lang": "en_US",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    url = f"https://www.linkedin.com/voyager/api{path}"
    res = requests.get(url, headers=headers)
    return res.json()

class SearchRequest(BaseModel):
    query: str

class ConnectRequest(BaseModel):
    profileId: str
    message: str

class PostSearchRequest(BaseModel):
    keywords: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/me")
def me():
    return voyager_get("/me")

@app.post("/search/people")
def search_people(req: SearchRequest):
    if not EXA_KEY:
        return {"error": "EXA_API_KEY not configured"}
    res = requests.post(
        "https://api.exa.ai/search",
        headers={
            "x-api-key": EXA_KEY,
            "Content-Type": "application/json"
        },
        json={
            "query": f"site:linkedin.com/in {req.query}",
            "numResults": 20,
            "contents": {"text": True}
        }
    )
    data = res.json()
    results = []
    for r in data.get("results", []):
        url = r.get("url", "")
        publicId = url.split("/in/")[-1].strip("/").split("/")[0]
        results.append({
            "name": r.get("title", ""),
            "profileUrl": url,
            "profileId": publicId,
            "headline": r.get("text", "")[:150] if r.get("text") else "",
            "source": "exa"
        })
    return {"results": results, "count": len(results)}

@app.post("/connect")
def connect(req: ConnectRequest):
    # Step 1: Get profile to extract correct entityUrn
    profile = voyager_get(f"/identity/profiles/{req.profileId}")
    
    mini = profile.get("miniProfile", {})
    entity_urn = mini.get("entityUrn", "")
    
    if not entity_urn:
        return {"error": f"Profile not found: {req.profileId}"}
    
    headers = {
        "cookie": f"li_at={LI_AT}; JSESSIONID={JSESSIONID}",
        "csrf-token": JSESSIONID.strip('"'),
        "x-restli-protocol-version": "2.0.0",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    res = requests.post(
        "https://www.linkedin.com/voyager/api/growth/normInvitations",
        headers=headers,
        json={
            "emberEntityName": "growth/invitation/norm-invitation",
            "invitee": {
                "com.linkedin.voyager.growth.invitation.InviteeProfile": {
                    "profileId": entity_urn
                }
            },
            "message": req.message
        }
    )
    return {"status": res.status_code, "response": res.text}

@app.get("/inbox")
def inbox():
    return voyager_get("/messaging/conversations?keyVersion=LEGACY_INBOX")

@app.post("/search/posts")
def search_posts(req: PostSearchRequest):
    encoded = req.keywords.replace(" ", "%20")
    return voyager_get(
        f"/search/blended?keywords={encoded}"
        f"&origin=GLOBAL_SEARCH_HEADER"
        f"&q=all"
        f"&filters=List(resultType->CONTENT)"
    )

@app.get("/contact/{profile_id}")
def get_contact_info(profile_id: str):
    return voyager_get(
        f"/identity/profiles/{profile_id}/profileContactInfo"
    )
