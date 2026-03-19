from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from .config import settings

app = FastAPI(
    title="Vanta LMS API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "version": "0.1.0"}


api_router = APIRouter(prefix="/api/v1")


@api_router.get("/")
async def api_v1_root() -> dict:
    return {"message": "Vanta LMS API v1"}


# Additional routers will be mounted here as features are added
# Example: from .routers import courses
#          api_router.include_router(courses.router)

app.include_router(api_router)
