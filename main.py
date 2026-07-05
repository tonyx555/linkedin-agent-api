@app.post("/connect")
def connect(req: ConnectRequest):
    # Step 1: Get profile view to extract urn
    profile = voyager_get(
        f"/identity/profileView/{req.profileId}"
    )
    
    # Extract from profileView (different from /profiles/)
    profile_urn = None
    
    # Try getting from profile directly
    profile_data = profile.get("profile", {})
    if profile_data:
        profile_urn = profile_data.get("entityUrn", "")
    
    # Fallback: try miniProfile
    if not profile_urn:
        mini = profile.get("miniProfile", {})
        profile_urn = mini.get("entityUrn", "")
    
    if not profile_urn:
        return {
            "error": "Could not get URN",
            "raw": profile  # return raw so we can debug
        }
    
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
                    "profileId": profile_urn
                }
            },
            "message": req.message,
            "trackingId": "ASSIX001"
        }
    )
    return {"status": res.status_code, "response": res.text}
