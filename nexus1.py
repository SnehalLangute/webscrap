import os, zipfile
import requests

# Configuration – replace with your actual details
NEXUS_URL = "https://your-nexus-server"        # Base URL of Nexus (e.g., "http://localhost:8081")
REPOSITORY = "documents"                       # Name of the hosted repository in Nexus
USERNAME = os.getenv("NEXUS_USERNAME")         # Nexus username (from environment for security)
PASSWORD = os.getenv("NEXUS_PASSWORD")         # Nexus password or token (from environment)
TAG_NAME = "doc-upload-20250404"               # Tag name to create/use
FILES_TO_UPLOAD = ["report.docx", "design.doc"]# Paths to .doc/.docx files to upload

# 1. Compress .doc/.docx files into a ZIP (if not already a single zip file)
if len(FILES_TO_UPLOAD) == 1 and FILES_TO_UPLOAD[0].lower().endswith(".zip"):
    zip_path = FILES_TO_UPLOAD[0]
else:
    zip_path = "upload_docs.zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for filepath in FILES_TO_UPLOAD:
            zipf.write(filepath, arcname=os.path.basename(filepath))
    print(f"Created ZIP archive '{zip_path}' with {len(FILES_TO_UPLOAD)} files.")

# 2. Create a new tag in Nexus (if it doesn't exist)
tag_url = f"{NEXUS_URL}/service/rest/v1/tags"
tag_payload = {"name": TAG_NAME}
response = requests.post(tag_url, auth=(USERNAME, PASSWORD), json=tag_payload)
if response.status_code in (200, 201, 204):
    print(f"Tag '{TAG_NAME}' created successfully (or already exists).")
elif response.status_code == 409:
    print(f"Tag '{TAG_NAME}' already exists (409 Conflict).")
else:
    raise Exception(f"Error creating tag: HTTP {response.status_code} - {response.text}")

# 3. Upload the ZIP file to the Nexus repository
upload_url = f"{NEXUS_URL}/service/rest/v1/components?repository={REPOSITORY}"
with open(zip_path, 'rb') as f:
    files = {'raw.asset1': (os.path.basename(zip_path), f)}
    data = {
        'raw.asset1.filename': os.path.basename(zip_path),
        # Optionally specify a subdirectory:
        # 'raw.directory': 'docs'
        # (We can also include 'tag': TAG_NAME here to tag on upload, if Nexus version supports it)
    }
    upload_resp = requests.post(upload_url, auth=(USERNAME, PASSWORD), files=files, data=data)
if upload_resp.status_code not in (200, 204):
    raise Exception(f"Upload failed: HTTP {upload_resp.status_code} - {upload_resp.text}")
print(f"Uploaded '{zip_path}' to repository '{REPOSITORY}'.")

# 4. Associate the uploaded component with the tag
assoc_url = f"{NEXUS_URL}/service/rest/v1/tags/associate/{TAG_NAME}"
# Identify the component by repository, and its path (group) and name in the repository
group_path = ""  # e.g., if 'raw.directory' was used in upload, put the same string here. Empty for root.
file_name = os.path.basename(zip_path)
params = {"repository": REPOSITORY, "group": group_path, "name": file_name}
assoc_resp = requests.post(assoc_url, auth=(USERNAME, PASSWORD), params=params)
if assoc_resp.status_code == 200:
    print(f"Successfully associated tag '{TAG_NAME}' with '{file_name}'.")
else:
    raise Exception(f"Tag association failed: HTTP {assoc_resp.status_code} - {assoc_resp.text}")
