import os
import sys
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

for filename, file_id in FILES.items():
    destination = os.path.join(VECTOR_DIR, filename)

    if os.path.exists(destination):
        if os.path.getsize(destination) >= MINIMUM_SIZES[filename]:
            print(f"{filename} already exists; skipping.")
            continue
        os.remove(destination)

    print(f"Downloading {filename}...")

    result = gdown.download(
        id=file_id,
        output=destination,
        quiet=False
    )

    if not result or not os.path.exists(destination):
        print(f"ERROR: Download failed for {filename}.")
        sys.exit(1)

    if os.path.getsize(destination) < MINIMUM_SIZES[filename]:
        os.remove(destination)
        print(f"ERROR: {filename} is smaller than expected.")
        sys.exit(1)

    print(f"Downloaded {filename}: {os.path.getsize(destination)} bytes")

print("All vector-store files are ready.")
