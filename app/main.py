import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.database import engine, Base
from app.routers import leads, replies, guardrails, decision_log, analytics

# Ensure all database tables exist on startup
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Database table check: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="EchoReach Autonomous Personalized Multi-Touch Sales Outreach Agent Backend API (Capabl Agentic AI Saksham - Track D2)"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(leads.router)
app.include_router(replies.router)
app.include_router(guardrails.router)
app.include_router(decision_log.router)
app.include_router(analytics.router)

# Mount Static Frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", tags=["Dashboard UI"])
    def serve_frontend_root():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/dashboard", tags=["Dashboard UI"])
    def serve_frontend_dashboard():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "dashboard_url": "/"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
