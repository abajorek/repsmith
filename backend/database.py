"""
Database initialization and session management.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base

# Database configuration
DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'repsmith.db')
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

# Ensure data directory exists
os.makedirs(DATABASE_DIR, exist_ok=True)

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = scoped_session(sessionmaker(bind=engine))


def init_db():
    """Initialize database schema."""
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at {DATABASE_PATH}")


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == '__main__':
    init_db()
