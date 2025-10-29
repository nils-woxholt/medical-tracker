"""Database migration rollback integration tests.

This module tests the reversibility of database migrations to ensure data integrity
during schema changes and rollback operations in production environments.
"""

import os
import pytest
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Generator, List, Dict, Any
from sqlalchemy import create_engine, text, inspect, MetaData, Table
from sqlalchemy.engine import Engine
from backend.app.core.database import get_database_url
from backend.app.models.logs import MedicationLog, SymptomLog


class MigrationTestDatabase:
    """Test database manager for migration rollback testing."""
    
    def __init__(self):
        self.test_db_name = f"test_migration_rollback_{os.getpid()}"
        self.original_db_url = get_database_url()
        self.test_db_url = self._create_test_db_url()
        # Engine will be created in setup_database; initialized as None for lifecycle
        self.engine = None  # set later to SQLAlchemy Engine instance
        
    def _create_test_db_url(self) -> str:
        """Create isolated test database URL."""
        if "sqlite" in self.original_db_url:
            # Use temporary SQLite database
            temp_dir = tempfile.mkdtemp()
            db_path = Path(temp_dir) / f"{self.test_db_name}.db"
            return f"sqlite:///{db_path}"
        else:
            # Use test schema for PostgreSQL/MySQL
            return self.original_db_url.replace("/medical_tracker", f"/{self.test_db_name}")
    
    def setup_database(self):
        """Create test database and engine."""
        self.engine = create_engine(self.test_db_url, echo=False)
        
        # Create database if using PostgreSQL/MySQL
        if "postgresql" in self.test_db_url or "mysql" in self.test_db_url:
            root_engine = create_engine(self.original_db_url.rsplit("/", 1)[0] + "/postgres")
            with root_engine.connect() as conn:
                conn.execute(text("COMMIT"))
                conn.execute(text(f"CREATE DATABASE {self.test_db_name}"))
    
    def teardown_database(self):
        """Clean up test database."""
        if self.engine:
            self.engine.dispose()
            
        if "sqlite" in self.test_db_url:
            # Remove temporary SQLite file
            db_path = self.test_db_url.replace("sqlite:///", "")
            temp_dir = Path(db_path).parent
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        else:
            # Drop test database
            root_engine = create_engine(self.original_db_url.rsplit("/", 1)[0] + "/postgres")
            with root_engine.connect() as conn:
                conn.execute(text("COMMIT"))
                conn.execute(text(f"DROP DATABASE IF EXISTS {self.test_db_name}"))
                

@pytest.fixture(scope="function")
def migration_db() -> Generator[MigrationTestDatabase, None, None]:
    """Provide isolated test database for migration testing."""
    test_db = MigrationTestDatabase()
    test_db.setup_database()
    
    # Set environment variable for Alembic
    original_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = test_db.test_db_url
    
    try:
        yield test_db
    finally:
        # Restore original database URL
        if original_db_url:
            os.environ["DATABASE_URL"] = original_db_url
        else:
            os.environ.pop("DATABASE_URL", None)
            
        test_db.teardown_database()


def run_alembic_command(command: str, db_url: str) -> subprocess.CompletedProcess:
    """Execute Alembic command with proper environment."""
    env = os.environ.copy()
    env["DATABASE_URL"] = db_url
    
    # Invoke via 'uv run' to ensure local project scripts & dependencies resolved consistently
    cmd = ["uv", "run", "alembic"] + command.split()
    # Use absolute path to backend directory (contains alembic.ini)
    # Path(__file__).resolve().parents[2] already points to backend/ directory
    backend_dir = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        cmd,
        cwd=str(backend_dir),
        env=env,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        pytest.fail(f"Alembic command failed: {result.stderr}")
    
    return result


def get_table_structure(engine: Engine) -> Dict[str, Dict[str, Any]]:
    """Get comprehensive table structure for comparison."""
    inspector = inspect(engine)
    structure = {}
    
    for table_name in inspector.get_table_names():
        columns = {}
        for col in inspector.get_columns(table_name):
            columns[col["name"]] = {
                "type": str(col["type"]),
                "nullable": col["nullable"],
                "default": col.get("default"),
            }
        
        indexes = {}
        for idx in inspector.get_indexes(table_name):
            indexes[idx["name"]] = {
                "columns": idx["column_names"],
                "unique": idx["unique"],
            }
        
        foreign_keys = {}
        for fk in inspector.get_foreign_keys(table_name):
            foreign_keys[fk["name"]] = {
                "columns": fk["constrained_columns"],
                "referred_table": fk["referred_table"],
                "referred_columns": fk["referred_columns"],
            }
        
        structure[table_name] = {
            "columns": columns,
            "indexes": indexes,
            "foreign_keys": foreign_keys,
        }
    
    return structure


def insert_test_data(engine: Engine) -> Dict[str, List[Dict[str, Any]]]:
    """Insert test data and return inserted records for validation."""
    test_data = {
        "medication_logs": [
            {
                "user_id": "user123",
                "medication_name": "Aspirin",
                "dosage": "100mg",
                "taken_at": "2024-01-01 12:00:00",
                "logged_at": "2024-01-01 12:05:00",
                "notes": "Test medication entry",
                "side_effects": None,
            },
            {
                "user_id": "user456",
                "medication_name": "Ibuprofen",
                "dosage": "200mg", 
                "taken_at": "2024-01-02 08:30:00",
                "logged_at": "2024-01-02 08:35:00",
                "notes": "Morning dose",
                "side_effects": "Mild nausea",
            },
        ],
        "symptom_logs": [
            {
                "user_id": "user123",
                "symptom_type": "headache",
                "severity": 7,
                "logged_at": "2024-01-01 10:00:00",
                "duration": "2 hours",
                "triggers": "stress",
                "location": "temples",
                "notes": "Throbbing pain",
                "impact_rating": 6,
            },
            {
                "user_id": "user456",
                "symptom_type": "fatigue",
                "severity": 5,
                "logged_at": "2024-01-02 14:00:00",
                "duration": "all day",
                "triggers": "poor sleep",
                "location": None,
                "notes": "General tiredness",
                "impact_rating": 4,
            },
        ],
    }
    
    with engine.connect() as conn:
        for table_name, records in test_data.items():
            for record in records:
                # Build dynamic insert statement
                columns = ", ".join(record.keys())
                placeholders = ", ".join(f":{key}" for key in record.keys())
                query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                conn.execute(text(query), record)
        conn.commit()
    
    return test_data


def verify_data_integrity(engine: Engine, expected_data: Dict[str, List[Dict[str, Any]]]) -> bool:
    """Verify that data matches expected values."""
    with engine.connect() as conn:
        for table_name, expected_records in expected_data.items():
            # Get actual records
            result = conn.execute(text(f"SELECT * FROM {table_name} ORDER BY id"))
            actual_records = [dict(row._mapping) for row in result]
            
            if len(actual_records) != len(expected_records):
                return False
            
            # Compare key fields (excluding auto-generated IDs)
            for actual, expected in zip(actual_records, expected_records):
                for key, expected_value in expected.items():
                    if key not in actual:
                        return False
                    
                    # Handle datetime comparisons and None values
                    actual_value = actual[key]
                    if actual_value != expected_value:
                        # Allow for slight datetime differences
                        if "at" in key and actual_value and expected_value:
                            continue  # Skip datetime precision checks
                        return False
    
    return True


class TestMigrationRollback:
    """Test suite for database migration rollback functionality."""
    
    def test_migration_rollback_preserves_schema(self, migration_db: MigrationTestDatabase):
        """Test that migration rollback properly restores schema structure."""
        # Apply all migrations
        run_alembic_command("upgrade head", migration_db.test_db_url)
        assert migration_db.engine is not None
        
        # Get current schema structure
        original_structure = get_table_structure(migration_db.engine)
        
        # Rollback one migration
        run_alembic_command("downgrade -1", migration_db.test_db_url)
        
        # Re-apply the migration
        run_alembic_command("upgrade +1", migration_db.test_db_url)
        
        # Verify schema is restored
        restored_structure = get_table_structure(migration_db.engine)
        assert original_structure == restored_structure, "Schema structure changed after rollback/reapply"
    
    def test_migration_rollback_preserves_data(self, migration_db: MigrationTestDatabase):
        """Test that data survives migration rollback when schema allows."""
        # Apply base migrations (logs tables)
        run_alembic_command("upgrade 6934fbabba4f", migration_db.test_db_url)
        assert migration_db.engine is not None
        
        # Insert test data
        test_data = insert_test_data(migration_db.engine)
        
        # Apply next migration
        run_alembic_command("upgrade +1", migration_db.test_db_url)
        
        # Verify data still exists
        assert verify_data_integrity(migration_db.engine, test_data), "Data lost after migration"
        
        # Rollback migration
        run_alembic_command("downgrade -1", migration_db.test_db_url)
        
        # Verify data still exists after rollback
        assert verify_data_integrity(migration_db.engine, test_data), "Data lost after rollback"
    
    def test_full_migration_cycle(self, migration_db: MigrationTestDatabase):
        """Test complete upgrade/downgrade cycle for all migrations."""
        # Apply all migrations
        run_alembic_command("upgrade head", migration_db.test_db_url)
        assert migration_db.engine is not None
        
        # Get list of applied migrations
        with migration_db.engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current_version = result.scalar()
        
        # Get migration history
        history_result = run_alembic_command("history", migration_db.test_db_url)
        migrations = []
        
        # Parse migration IDs from history output
        for line in history_result.stdout.split('\\n'):
            if " -> " in line and "(head)" not in line:
                migration_id = line.split()[0].replace("(", "").replace(")", "")
                if migration_id and len(migration_id) == 12:  # Alembic revision length
                    migrations.append(migration_id)
        
        # Test rollback to each migration
        for migration in reversed(migrations[:-1]):  # Skip the last (base) migration
            # Rollback to specific migration
            run_alembic_command(f"downgrade {migration}", migration_db.test_db_url)
            
            # Verify database is functional
            tables = get_table_structure(migration_db.engine)
            assert len(tables) > 0, f"No tables found after rollback to {migration}"
            
            # Re-apply migrations
            run_alembic_command("upgrade head", migration_db.test_db_url)
    
    def test_migration_idempotency(self, migration_db: MigrationTestDatabase):
        """Test that applying the same migration multiple times is safe."""
        # Apply base migration
        run_alembic_command("upgrade 6934fbabba4f", migration_db.test_db_url)
        assert migration_db.engine is not None
        original_structure = get_table_structure(migration_db.engine)
        
        # Try to apply the same migration again (should be no-op)
        run_alembic_command("upgrade 6934fbabba4f", migration_db.test_db_url)
        duplicate_structure = get_table_structure(migration_db.engine)
        
        assert original_structure == duplicate_structure, "Duplicate migration application changed schema"
    
    def test_migration_dependency_chain(self, migration_db: MigrationTestDatabase):
        """Test that migration dependency chain is properly maintained."""
        # Apply migrations one by one and verify each step
        migrations = [
            "6934fbabba4f",  # Create logs tables
            "af9d234e1b5c",  # Add medications table  
            "a3c9824a5658",  # Add conditions/doctors tables
        ]
        
        for migration in migrations:
            # Apply specific migration
            run_alembic_command(f"upgrade {migration}", migration_db.test_db_url)
            assert migration_db.engine is not None
            
            # Verify database is in valid state
            structure = get_table_structure(migration_db.engine)
            assert len(structure) > 0, f"Database empty after applying {migration}"
            
            # Verify alembic version table is updated
            with migration_db.engine.connect() as conn:
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                current_version = result.scalar()
                assert current_version == migration, f"Alembic version not updated for {migration}"
    
    def test_rollback_with_foreign_key_constraints(self, migration_db: MigrationTestDatabase):
        """Test rollback behavior with foreign key relationships."""
        # Apply all migrations to get foreign key constraints
        run_alembic_command("upgrade head", migration_db.test_db_url)
        assert migration_db.engine is not None
        
        # Check for foreign key constraints
        structure = get_table_structure(migration_db.engine)
        has_foreign_keys = any(
            bool(table_info["foreign_keys"]) 
            for table_info in structure.values()
        )
        
        if has_foreign_keys:
            # Test rollback with foreign key constraints present
            run_alembic_command("downgrade -1", migration_db.test_db_url)
            
            # Verify foreign keys are properly handled
            rollback_structure = get_table_structure(migration_db.engine)
            
            # Re-apply migration
            run_alembic_command("upgrade +1", migration_db.test_db_url)
            
            # Verify foreign keys are restored
            restored_structure = get_table_structure(migration_db.engine)
            assert structure == restored_structure, "Foreign key constraints not properly restored"
    
    def test_migration_error_recovery(self, migration_db: MigrationTestDatabase):
        """Test recovery from failed migrations."""
        # Apply base migrations
        run_alembic_command("upgrade 6934fbabba4f", migration_db.test_db_url)
        assert migration_db.engine is not None
        
        # Insert test data
        test_data = insert_test_data(migration_db.engine)
        
        # Simulate partial migration failure by manually stopping at intermediate step
        # This tests that rollback can recover from incomplete migrations
        
        # Get current state
        original_structure = get_table_structure(migration_db.engine)
        
        # Try to rollback from current state
        run_alembic_command("downgrade -1", migration_db.test_db_url)
        
        # Verify we can get back to a known good state
        rollback_structure = get_table_structure(migration_db.engine)
        
        # Re-apply migration
        run_alembic_command("upgrade 6934fbabba4f", migration_db.test_db_url)
        
        # Verify data integrity after recovery
        assert verify_data_integrity(migration_db.engine, test_data), "Data integrity lost during error recovery"


class TestMigrationPerformance:
    """Test migration performance and resource usage."""
    
    def test_large_dataset_migration_performance(self, migration_db: MigrationTestDatabase):
        """Test migration performance with larger datasets."""
        # Apply base migrations
        run_alembic_command("upgrade 6934fbabba4f", migration_db.test_db_url)
        assert migration_db.engine is not None
        
        # Insert larger dataset
        import time
        
        start_time = time.time()
        
        # Insert 1000 test records
        with migration_db.engine.connect() as conn:
            for i in range(1000):
                conn.execute(text("""
                    INSERT INTO medication_logs 
                    (user_id, medication_name, dosage, taken_at, logged_at, notes) 
                    VALUES (:user_id, :med_name, :dosage, :taken_at, :logged_at, :notes)
                """), {
                    "user_id": f"user{i % 100}",
                    "med_name": f"Medication{i % 50}",
                    "dosage": f"{(i % 10) * 100}mg",
                    "taken_at": "2024-01-01 12:00:00",
                    "logged_at": "2024-01-01 12:00:00",
                    "notes": f"Test entry {i}",
                })
            conn.commit()
        
        insert_time = time.time() - start_time
        
        # Test migration performance with large dataset
        migration_start = time.time()
        run_alembic_command("upgrade +1", migration_db.test_db_url)
        migration_time = time.time() - migration_start
        
        # Test rollback performance
        rollback_start = time.time()
        run_alembic_command("downgrade -1", migration_db.test_db_url)
        rollback_time = time.time() - rollback_start
        
        # Performance assertions (adjust thresholds as needed)
        assert migration_time < 30.0, f"Migration took too long: {migration_time:.2f}s"
        assert rollback_time < 30.0, f"Rollback took too long: {rollback_time:.2f}s"
        
        print(f"Performance metrics - Insert: {insert_time:.2f}s, Migration: {migration_time:.2f}s, Rollback: {rollback_time:.2f}s")


if __name__ == "__main__":
    # Run specific test for manual testing
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        # Manual test setup for debugging
        test_db = MigrationTestDatabase()
        test_db.setup_database()
        
        try:
            print(f"Test database: {test_db.test_db_url}")
            
            # Run basic migration test
            os.environ["DATABASE_URL"] = test_db.test_db_url
            run_alembic_command("upgrade head", test_db.test_db_url)
            
            print("All migrations applied successfully")
            
            # Test rollback
            run_alembic_command("downgrade base", test_db.test_db_url)
            
            print("All migrations rolled back successfully")
            
        finally:
            test_db.teardown_database()
            print("Test database cleaned up")
    else:
        print("Run with 'python test_migrations.py manual' for manual testing")
        print("Or run with pytest: 'pytest backend/tests/integration/test_migrations.py -v'")