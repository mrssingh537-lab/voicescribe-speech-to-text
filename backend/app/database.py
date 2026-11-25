from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# SQLite connection args for multi-threaded FastAPI access
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """Initializes tables and ensures any missing columns are added."""
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        try:
            from sqlalchemy import text
            result = conn.execute(text("PRAGMA table_info(transcripts)"))
            cols = [row[1] for row in result.fetchall()]
            if cols and "model_name" not in cols:
                conn.execute(text("ALTER TABLE transcripts ADD COLUMN model_name VARCHAR(100) DEFAULT 'Whisper Turbo (Local)'"))
                conn.commit()
        except Exception:
            pass


def get_db():
    """Dependency that provides a database session and ensures closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
