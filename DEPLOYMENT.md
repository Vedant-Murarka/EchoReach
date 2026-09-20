# EchoReach — Cloud Deployment Guide (Free Tier Options)

This guide walks you through deploying **EchoReach** to the cloud using 100% **free tier hosting options** (Render, Supabase PostgreSQL, Fly.io, Railway, and Docker).

---

## 🗄️ 1. Database Setup: Supabase PostgreSQL (Free Tier)

Supabase provides a free, managed PostgreSQL database with 500MB storage and zero setup fees.

### Step-by-Step Supabase Setup:
1. Go to [https://supabase.com](https://supabase.com) and create a free account.
2. Click **"New Project"**, give it a name (e.g. `echoreach-db`), and set a secure database password.
3. Once the database is provisioned, go to **Project Settings** $\rightarrow$ **Database** $\rightarrow$ **Connection String**.
4. Select the **URI** format (Node/Python/URI):
   ```text
   postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```
5. *(Optional)* Go to the **SQL Editor** in Supabase and paste the contents of [`supabase_schema.sql`](file:///c:/Coding/EchoReach/supabase_schema.sql) and click **Run**. (Note: SQLAlchemy will also auto-generate all tables on server startup if the database is blank).
6. Set this connection string as your `DATABASE_URL` in `.env` or in your cloud host's environment variables.

---

## 🚀 2. Option A: Deploying on Render (Recommended Free Web Service)

Render offers a generous free tier for Python web services and natively supports FastAPI/Uvicorn.

### Method 1: Using Render Blueprint (`render.yaml`)
1. Push your EchoReach code to a GitHub repository.
2. Log into [Render Dashboard](https://dashboard.render.com).
3. Click **"New +"** $\rightarrow$ **"Blueprint"**.
4. Connect your GitHub repository. Render will automatically detect [`render.yaml`](file:///c:/Coding/EchoReach/render.yaml).
5. Fill in the optional environment variables (`DATABASE_URL`, `GEMINI_API_KEY`, `GROQ_API_KEY`) and click **Apply**.

### Method 2: Manual Web Service on Render
1. In Render Dashboard, click **"New +"** $\rightarrow$ **"Web Service"**.
2. Connect your GitHub repository.
3. Configure the following settings:
   - **Name**: `echoreach-backend`
   - **Language / Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
4. Under **Environment Variables**, add:
   - `DATABASE_URL`: Your Supabase connection string (or leave blank to use SQLite)
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `GROQ_API_KEY`: Your Groq API key
   - `DAILY_SEND_CAP`: `50`
   - `SLACK_WEBHOOK_URL`: (Optional)
5. Click **"Create Web Service"**.
6. Once deployed, Render gives you a live URL like: `https://echoreach-backend.onrender.com`.
7. Access interactive docs at: `https://echoreach-backend.onrender.com/docs`.

---

## ✈️ 3. Option B: Deploying on Fly.io

Fly.io provides containerized hosting with global edge routing.

### Step-by-Step Fly.io Deployment:
1. Install the Fly CLI:
   - **Windows**: `pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"`
   - **macOS/Linux**: `curl -L https://fly.io/install.sh | sh`
2. Log into Fly:
   ```bash
   fly auth login
   ```
3. In the EchoReach root directory (where [`fly.toml`](file:///c:/Coding/EchoReach/fly.toml) is located), run:
   ```bash
   fly launch --no-deploy
   ```
4. Set your cloud secrets:
   ```bash
   fly secrets set DATABASE_URL="postgresql://postgres:password@db.ref.supabase.co:5432/postgres"
   fly secrets set GEMINI_API_KEY="your-gemini-key"
   fly secrets set GROQ_API_KEY="your-groq-key"
   ```
5. Deploy:
   ```bash
   fly deploy
   ```

---

## 🐳 4. Option C: Running with Docker (Local or Any Cloud VPS)

You can run EchoReach anywhere using the optimized [`Dockerfile`](file:///c:/Coding/EchoReach/Dockerfile).

### Build and Run:
```bash
# 1. Build the Docker image
docker build -t echoreach-backend .

# 2. Run container on port 8000
docker run -d -p 8000:8000 --env-file .env --name echoreach echoreach-backend
```

Test your container:
```bash
curl http://localhost:8000/
```

---

## 🔒 5. Cloud Verification & Health Check

Once deployed to your chosen cloud platform:

1. **Health Check**:
   ```bash
   GET https://<YOUR-APP-URL>/
   ```
   *Expected Response:*
   ```json
   {
     "status": "online",
     "system": "EchoReach Backend API",
     "version": "1.0.0",
     "docs_url": "/docs"
   }
   ```

2. **Interactive API Explorer**:
   Navigate to `https://<YOUR-APP-URL>/docs` to test all endpoints live!

3. **Check Guardrails**:
   ```bash
   GET https://<YOUR-APP-URL>/guardrails/status
   ```
