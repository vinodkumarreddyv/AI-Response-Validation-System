import os
import sys

# Ensure immediate real-time logging output on cloud platforms
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

print("=== Starting AI Response Validation System ===", flush=True)

port = int(os.environ.get("PORT", 10000))
print(f"Binding to 0.0.0.0:{port}...", flush=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, log_level="info")
