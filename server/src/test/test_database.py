"""
Tests for the database module.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.src.database.core import Base, get_db, engine


class TestDatabase:
    """Test cases for database module."""
    
    def test_database_connection(self):
        """Test that database connection is established."""
        # Test that engine is created
        assert engine is not None
        
        # Test that we can connect to the database
        connection = engine.connect()
        assert connection is not None
        connection.close()
    
    def test_get_db_dependency(self):
        """Test the get_db dependency function."""
        db_generator = get_db()
        db_session = next(db_generator)
        
        # Test that we get a valid session
        assert db_session is not None
        
        # Clean up
        try:
            next(db_generator)
        except StopIteration:
            pass  # Expected behavior
    
    def test_base_metadata(self):
        """Test that Base metadata is properly configured."""
        assert Base.metadata is not None
        
        # Test that tables can be created
        test_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=test_engine)
        
        # Verify tables were created
        table_names = list(Base.metadata.tables.keys())
        assert len(table_names) > 0
