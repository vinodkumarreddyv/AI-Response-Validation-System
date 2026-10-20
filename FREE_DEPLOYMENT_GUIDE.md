# 🚀 100% Free Deployment Guide

This guide details how to deploy the **AI Response Validation System** completely for **FREE** with zero hidden costs.

---

## ⚡ Architecture & Free Tier Requirements

Because this system runs **SentenceTransformers**, a **152MB FAISS vector store**, and **PyTorch**, serverless functions with small size limits (like pure Vercel Python with its 250MB Lambda cap) will fail. 

Here are the best **100% Free** options tested and pre-configured for this repo:

| Platform | Cost | Specs | Recommended For |
| :--- | :--- | :--- | :--- |
| **Hugging Face Spaces (Docker)** | **100% FREE** | **16 GB RAM**, 2 vCPU, 50 GB Disk | ⭐ **Best & Easiest** (Single fullstack container) |
| **Render (Docker Web Service)** | **100% FREE** | 512 MB RAM (Optimized with shared model) | Good alternative |
| **Vercel + Hugging Face Backend** | **100% FREE** | Edge CDN (Frontend) + 16 GB RAM (Backend) | Best performance |

---

## Option 1: Hugging Face Spaces (⭐ Recommended - 100% Free, 16GB RAM)

Hugging Face Spaces is the premier free host for Machine Learning apps. It gives you **16 GB RAM** for free with a public HTTPS link.

### Step 1: Create a Hugging Face Account & Space
1. Sign up for free at [huggingface.co](https://huggingface.co/join) (no credit card required).
2. Go to [huggingface.co/new-space](https://huggingface.co/new-space).
3. Fill in:
   - **Space name**: `ai-response-validation-system` (or any name you like)
   - **License**: `mit`
   - **Space SDK**: Select **Docker** -> **Blank**
   - **Space hardware**: Select **Free (2 vCPU · 16GB RAM · 50GB Disk)**
   - Click **Create Space**.

### Step 2: Push Your Code to the Space
In your local project terminal (inside the project directory):

```bash
# Add Hugging Face as a git remote (replace YOUR_USERNAME and YOUR_SPACE_NAME)
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME

# Push to Hugging Face
git push --force hf master:main
```
*(When prompted for credentials, enter your Hugging Face username and an Access Token generated at `huggingface.co/settings/tokens`).*

### Step 3: Done!
Hugging Face will automatically build the `Dockerfile`, bundle the React frontend, start FastAPI on port 7860, and give you a live URL:
`https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space`

---

## Option 2: Render Free Tier (100% Free)

Render provides free Docker web services.

### Step 1: Push to GitHub
1. Create a free repository on [github.com/new](https://github.com/new).
2. Push your project to GitHub:
   ```bash
   git remote add origin https://github.com/YOUR_GITHUB_USER/YOUR_REPO.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Render
1. Sign up for free at [render.com](https://render.com).
2. Click **New +** -> **Web Service**.
3. Select **Build and deploy from a Git repository** and connect your GitHub repo.
4. Render will auto-detect the `Dockerfile` (or `render.yaml`).
   - **Name**: `ai-validation-system`
   - **Environment**: `Docker`
   - **Instance Type**: `Free`
5. Click **Deploy Web Service**.
Render will build the container and provide you a free live URL: `https://your-app.onrender.com`.

---

## Option 3: Vercel (Frontend) + Hugging Face / Render (Backend)

If you prefer having your React frontend on Vercel's global CDN:

1. **Deploy Backend first** using Option 1 (Hugging Face) or Option 2 (Render). Copy your backend URL (e.g. `https://your-backend.hf.space`).
2. Go to [vercel.com](https://vercel.com) and click **Add New Project**.
3. Import your GitHub repository.
4. In the configuration:
   - **Root Directory**: Select `frontend`
   - **Framework Preset**: `Vite`
   - **Environment Variables**:
     - Key: `VITE_API_URL`
     - Value: `https://your-backend.hf.space` (your backend URL without trailing slash)
5. Click **Deploy**. Vercel will deploy your React UI with instantaneous global CDN routing.

---

## 🛠️ Testing Locally Before Deploying

To test the unified fullstack build locally:

```bash
# 1. Build the React frontend
cd frontend
npm install
npm run build
cd ..

# 2. Run the FastAPI backend
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open your browser to:
- **Web UI & Dashboard**: `http://localhost:8000`
- **Swagger API Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`
