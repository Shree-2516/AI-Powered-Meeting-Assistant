from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.settings import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    """Dependency for getting async database session."""
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database: enable pgvector and create tables."""
    from sqlalchemy import text
    from app.models.db_models import MeetingRecord  # Import here to register models
    
    async with engine.begin() as conn:
        # Try to enable pgvector extension
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            print("[Database] pgvector extension enabled")
        except Exception as e:
            print(f"[Database] WARNING: Could not enable pgvector extension: {e}")
            print("[Database] HINT: You may need to install pgvector on your PostgreSQL server.")
            print("[Database] Semantic search features will be disabled.")
            
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("[Database] Tables created/verified")
