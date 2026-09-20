from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import leads, replies, guardrails, decision_log, analytics

# Ensure all database tables exist on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="EchoReach Autonomous Personalized Multi-Touch Sales Outreach Agent Backend API (Capabl Agentic AI Saksham - Track D2)"
)

# CORS Middleware (allowing Next.js frontend requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(leads.router)
app.include_router(replies.router)
app.include_router(guardrails.router)
app.include_router(decision_log.router)
app.include_router(analytics.router)

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
