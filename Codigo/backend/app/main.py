import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import annotations, auth, documents, projects
from app.core.config import settings
from app.db.database import connect_to_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logging.getLogger("app").setLevel(logging.INFO)

# Bridge GOOGLE_APPLICATION_CREDENTIALS into os.environ for the Google SDK.
# pydantic-settings carrega o valor no objeto settings, mas o SDK lê de os.environ.
if settings.GOOGLE_APPLICATION_CREDENTIALS:
    cred_path = Path(settings.GOOGLE_APPLICATION_CREDENTIALS)
    if not cred_path.is_absolute():
        cred_path = (Path(__file__).resolve().parent.parent / cred_path).resolve()
    if cred_path.exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(cred_path)
        logging.getLogger("app").info(
            "Google credentials loaded from %s", cred_path
        )
    else:
        logging.getLogger("app").warning(
            "GOOGLE_APPLICATION_CREDENTIALS file not found: %s", cred_path
        )


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
app.include_router(
    annotations.router,
    prefix="/api/projects/{project_uid}/annotations",
    tags=["annotations"],
)