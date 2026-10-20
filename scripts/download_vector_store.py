import os
import sys
import re
import requests
import gdown

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_DIR = os.path.join(BASE_DIR, "data", "vector_store")

FILES = {
    "knowledge_base.index": "1j7Zj4GN6alcdkW99j8P55Hp33aOm6MUv",
    "chunks.json": "186wQQV-R-r4GEEl0lFRYc9I6Bd9rJDBn",
    "metadata.json": "1xbbOAvdel4HO68qWmHrq1z1CZc_aBE_p",
}

MINIMUM_SIZES = {
    "knowledge_base.index": 100_000_000,
    "chunks.json": 100_000_000,
    "metadata.json": 1_000_000,
}

os.makedirs(VECTOR_DIR, exist_ok=True)


def download_file(file_id: str, destination: str):
    """Downloads large file from Google Drive, handling virus scan confirmation."""
    session = requests.Session()
    url = "https://drive.google.com/uc?export=download"

    response = session.get(url, params={"id": file_id}, stream=True)

    # Check for direct file download
    content_type = response.headers.get("Content-Type", "")
    if "text/html" not in content_type:
        _stream_save(response, destination)
        return True

    # Parse confirmation form / token
    inputs = dict(re.findall(r'name="([^"]+)"\s+value="([^"]+)"', response.text))
    form_match = re.search(r'action="([^"]+)"', response.text)

    if form_match and inputs:
        action_url = form_match.group(1)
        response = session.get(action_url, params=inputs, stream=True)
        if "text/html" not in response.headers.get("Content-Type", ""):
            _stream_save(response, destination)
            return True

    # Fallback to gdown
    print("Falling back to gdown...")
    result = gdown.download(id=file_id, output=destination, quiet=False)
    return bool(result and os.path.exists(destination))


def _stream_save(response, destination):
    with open(destination, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)


for filename, file_id in FILES.items():
    destination = os.path.join(VECTOR_DIR, filename)

    if os.path.exists(destination):
        if os.path.getsize(destination) >= MINIMUM_SIZES[filename]:
            print(f"{filename} already exists ({os.path.getsize(destination)} bytes); skipping.")
            continue
        os.remove(destination)

    print(f"Downloading {filename}...")
    success = download_file(file_id, destination)

    if not success or not os.path.exists(destination):
        print(f"ERROR: Download failed for {filename}.")
        sys.exit(1)

    if os.path.getsize(destination) < MINIMUM_SIZES[filename]:
        os.remove(destination)
        print(f"ERROR: {filename} is smaller than expected.")
        sys.exit(1)

    print(f"Downloaded {filename}: {os.path.getsize(destination)} bytes")

print("All vector-store files are ready.")
