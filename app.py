import os
import uvicorn
import gradio as gr
from backend.app.main import app

# Minimal Gradio interface so Hugging Face Space initializes cleanly
with gr.Blocks(title="AI Response Validation System") as demo:
    gr.Markdown(
        """
        # 🛡️ AI Response Validation System API
        
        The AI Response Validation backend is running with **16 GB RAM** on Hugging Face Spaces.
        
        - 🌐 **Interactive Swagger Docs:** [/docs](/docs)
        - 🩺 **Health Check:** [/health](/health)
        - 📊 **Dashboard API:** [/api/dashboard/summary](/api/dashboard/summary)
        """
    )

# Mount Gradio onto the existing FastAPI backend
# /gradio gives the Gradio view, while / and /api serve the core system and React UI
app = gr.mount_gradio_app(app, demo, path="/gradio")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
