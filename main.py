import requests
import os
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

LI_AT = os.environ.get("LINKEDIN_LI_AT", "")
JSESSIONID = os.environ.get("LINKEDIN_JSESSIONID", "")

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

@app.post("/search")
def search(req: SearchRequest):
    encoded = req.query.replace(" ", "%20")
    return voyager_get(
        f"/search/blended?keywords={encoded}"
        f"&origin=GLOBAL_SEARCH_HEADER"
        f"&q=all"
    )

@app.get("/inbox")
def inbox():
    return voyager_get("/messaging/conversations?keyVersion=LEGACY_INBOX")

@app.post("/connect")
def connect(req: ConnectRequest):
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
                    "profileId": req.profileId
                }
            },
            "message": req.message
        }
    )
    return {"status": res.status_code, "response": res.text}

@app.post("/search/posts")
def search_posts(req: PostSearchRequest):
    encoded = req.keywords.replace(" ", "%20")
    return voyager_get(
        f"/search/blended?keywords={encoded}"
        f"&origin=GLOBAL_SEARCH_HEADER"
        f"&q=all"
        f"&filters=List(resultType->CONTENT)"
    )

@app.post("/search/people")
def search_people(req: SearchRequest):
    encoded = req.query.replace(" ", "%20")
    # Try without the filter first
    return voyager_get(
        f"/search/blended?keywords={encoded}"
        f"&origin=GLOBAL_SEARCH_HEADER"
        f"&q=all"
    )

@app.get("/contact/{profile_id}")
def get_contact_info(profile_id: str):
    return voyager_get(
        f"/identity/profiles/{profile_id}/profileContactInfo"
    )
