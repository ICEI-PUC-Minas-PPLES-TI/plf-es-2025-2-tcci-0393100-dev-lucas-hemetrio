from neomodel import config, db
from app.core.config import settings

def connect_to_db():
    config.DATABASE_URL = settings.NEO4J_URL
    import app.models.user  # noqa: F401
    import app.models.project  # noqa: F401
    import app.models.document  # noqa: F401
    import app.models.annotation  # noqa: F401
    db.install_all_labels()