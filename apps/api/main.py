from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.dashboard.main import router as dashboard_router
from core.logging.logger import logger

app = FastAPI(title="Webook Sniper API", version="2.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(dashboard_router)

@app.get("/health")
async def health_check():
    return {"status": "operational", "engine": "high-concurrency"}

if __name__ == "__main__":
    import uvicorn
    logger.info("API_Gateway_Starting", port=8000)
    uvicorn.run(app, host="0.0.0.0", port=8000)
