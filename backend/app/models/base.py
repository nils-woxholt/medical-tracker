"""
SQLModel Base Classes and Database Connection Management

This module provides the base classes and database connection utilities
for the SaaS Medical Tracker application using SQLModel and SQLAlchemy.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import structlog
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlmodel import SQLModel

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# Global metadata for Alembic migrations
metadata = MetaData()

class Base(SQLModel):
    """
    Base SQLModel class with common fields and configurations.
    
    All database models should inherit from this class to ensure
    consistent behavior and shared functionality.
    """

    class Config:
            """SQLModel configuration for all models."""
            # Enable validation on assignment
            validate_assignment = True

            # Use enum values for serialization
            use_enum_values = True

            # Allow population by field name or alias (renamed in v2)
            validate_by_name = True

            # Enable arbitrary types (for datetime, UUID, etc.)
            arbitrary_types_allowed = True
class TimestampMixin(SQLModel):
    """
    Mixin class to add timestamp fields to models.
    
    Provides created_at and updated_at fields with automatic
    timestamp management.
    """

    # TODO: Add actual timestamp fields once we have proper datetime handling
    # created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    # updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    pass


class DatabaseManager:
    """
    Database connection and session management.
    
    Provides both sync and async database connections with proper
    connection pooling and session lifecycle management.
    """

    def __init__(self, database_url: str, echo: bool = False):
        """
        Initialize database manager.
        
        Args:
            database_url: Database connection URL
            echo: Whether to echo SQL queries (for debugging)
        """
        self.database_url = database_url
        self.echo = echo

        # Sync engine and session
        self.engine = create_engine(
            database_url,
            echo=echo,
            pool_pre_ping=True,  # Validate connections before use
        )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

        # Async engine and session (for future use)
        if database_url.startswith("sqlite"):
            # SQLite async URL
            async_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        else:
            # PostgreSQL async URL
            async_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

        self.async_engine = create_async_engine(
            async_url,
            echo=echo,
            pool_pre_ping=True,
        )

        self.AsyncSessionLocal = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.async_engine,
            class_=AsyncSession,
        )

        logger.info(
            "Database manager initialized",
            database_type="sqlite" if "sqlite" in database_url else "postgresql",
            echo=echo,
        )

    def create_tables(self):
        """
        Create all database tables.
        
        This should only be used in development or testing.
        Production should use Alembic migrations.
        """
        try:
            SQLModel.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error("Failed to create database tables", error=str(e))
            raise

    def get_session(self) -> Session:
        """
        Get a synchronous database session.
        
        Returns:
            Session: SQLAlchemy session
        """
        return self.SessionLocal()

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an asynchronous database session as context manager.
        
        Usage:
            async with db_manager.get_async_session() as session:
                result = await session.execute(select(User))
        
        Yields:
            AsyncSession: SQLAlchemy async session
        """
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self):
        """Close all database connections."""
        if hasattr(self, 'async_engine'):
            await self.async_engine.dispose()

        if hasattr(self, 'engine'):
            self.engine.dispose()

        logger.info("Database connections closed")


# Global database manager instance
db_manager: Optional[DatabaseManager] = None


def init_database(database_url: Optional[str] = None, echo: Optional[bool] = None) -> DatabaseManager:
    """
    Initialize the global database manager.
    
    Args:
        database_url: Database URL (defaults to settings)
        echo: Echo SQL queries (defaults to settings)
    
    Returns:
        DatabaseManager: Configured database manager
    """
    global db_manager

    if database_url is None:
        database_url = settings.DATABASE_URL

    if echo is None:
        echo = settings.DEBUG and settings.ENVIRONMENT == "development"

    db_manager = DatabaseManager(database_url=database_url, echo=echo)

    logger.info("Database initialized", database_url=database_url)
    return db_manager


def get_database() -> DatabaseManager:
    """
    Get the global database manager instance.
    
    Returns:
        DatabaseManager: Global database manager
        
    Raises:
        RuntimeError: If database hasn't been initialized
    """
    global db_manager

    if db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    return db_manager


# Dependency for FastAPI route injection
def get_db_session() -> Session:
    """
    FastAPI dependency to get database session.
    
    Usage:
        @app.get("/users/")
        def get_users(db: Session = Depends(get_db_session)):
            return db.query(User).all()
    
    Yields:
        Session: Database session
    """
    db = get_database()
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get async database session.
    
    Usage:
        @app.get("/users/")
        async def get_users(db: AsyncSession = Depends(get_async_db_session)):
            result = await db.execute(select(User))
            return result.scalars().all()
    
    Yields:
        AsyncSession: Async database session
    """
    db = get_database()
    async with db.get_async_session() as session:
        yield session


# Health check function for database connectivity
def check_database_health() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        db = get_database()
        with db.get_session() as session:
            # Simple query to check connectivity
            session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False


async def check_async_database_health() -> bool:
    """
    Check if async database connection is healthy.
    
    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        db = get_database()
        async with db.get_async_session() as session:
            # Simple query to check connectivity
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error("Async database health check failed", error=str(e))
        return False


# Example usage and testing
if __name__ == "__main__":
    # Initialize database for testing
    init_database("sqlite:///test.db", echo=True)

    # Test sync session
    with get_database().get_session() as session:
        result = session.execute(text("SELECT 1 as test"))
        print(f"Sync test result: {result.scalar()}")

    # Test health check
    is_healthy = check_database_health()
    print(f"Database health: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")

    print("✅ Database base module test completed")
