import os
import requests
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse

# Load secure config from environment or config file
NEXUS_URL = os.getenv("NEXUS_URL")  # e.g. "https://nexus.company.com"
NEXUS_REPO = os.getenv("NEXUS_REPO")  # e.g. "internal-raw-hosted"
NEXUS_USER = os.getenv("NEXUS_USER")  # Nexus service account username
NEXUS_PASS = os.getenv("NEXUS_PASS")  # Nexus service account password or token

app = FastAPI()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), path: str = Form(None)):
    # Validate and sanitize the optional path
    subdir = ""
    if path:
        # Basic sanitization: strip any leading/trailing slashes and disallow path traversal
        clean_path = path.strip().lstrip("/").rstrip("/")
        if ".." in clean_path:
            raise HTTPException(status_code=400, detail="Invalid path")
        subdir = clean_path  # (Further sanitization or allowlist of characters can be applied)
    else:
        clean_path = ""  # no subdir
    
    filename = file.filename
    # (Optionally, sanitize filename as well if needed; e.g., remove dangerous chars)
    
    # Construct target Nexus URL
    repo_path = f"{clean_path}/{filename}" if clean_path else filename
    nexus_upload_url = f"{NEXUS_URL}/repository/{NEXUS_REPO}/{repo_path}"
    
    # Read file and stream to Nexus via PUT
    try:
        # Use Basic Auth with Nexus credentials. Ensure HTTPS is used in NEXUS_URL for security.
        response = requests.put(
            nexus_upload_url,
            data=await file.read(),  # reading entire file into memory; for large files, stream in chunks
            auth=(NEXUS_USER, NEXUS_PASS)
        )
    except requests.RequestException as err:
        raise HTTPException(status_code=500, detail=f"Nexus upload request failed: {err}")
    
    # Check Nexus response
    if response.status_code not in (200, 201, 204):
        raise HTTPException(status_code=500, detail=f"Upload to Nexus failed: {response.text}")
    
    # Return the URL from which the file can be downloaded
    file_url = nexus_upload_url  # since Nexus serves it at the same path
    return JSONResponse(content={"url": file_url})
