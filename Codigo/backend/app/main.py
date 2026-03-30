from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth
from app.api.routes import documents
from app.api.routes import projects
from app.core.config import settings
from app.db.database import connect_to_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_to_db()
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(
    documents.router,
    prefix="/api/projects/{project_uid}/documents",
    tags=["documents"],
)