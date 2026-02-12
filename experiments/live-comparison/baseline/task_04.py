import hashlib
import json
import logging
import os
import sqlite3
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Type

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MigrationRecord:
    """Record of an applied migration."""
    id: int
    version: str
    name: str
    checksum: str
    applied_at: datetime
    execution_time_ms: int


class DatabaseAdapter(Protocol):
    """Protocol for database adapters."""
    
    def execute(self, sql: str, params: Optional[tuple] = None) -> None:
        """Execute a SQL statement."""
        ...
    
    def fetchall(self, sql: str, params: Optional[tuple] = None) -> List[tuple]:
        """Fetch all results from a query."""
        ...
    
    def fetchone(self, sql: str, params: Optional[tuple] = None) -> Optional[tuple]:
        """Fetch one result from a query."""
        ...
    
    def begin_transaction(self) -> None:
        """Begin a transaction."""
        ...
    
    def commit(self) -> None:
        """Commit the current transaction."""
        ...
    
    def rollback(self) -> None:
        """Rollback the current transaction."""
        ...
    
    def close(self) -> None:
        """Close the database connection."""
        ...


class SQLiteAdapter:
    """SQLite implementation of DatabaseAdapter."""
    
    def __init__(self, database_path: str) -> None:
        """
        Initialize SQLite adapter.
        
        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self._connect()
    
    def _connect(self) -> None:
        """Establish database connection."""
        self.connection = sqlite3.connect(self.database_path)
        self.connection.isolation_level = None  # Autocommit mode
        self.cursor = self.connection.cursor()
    
    def execute(self, sql: str, params: Optional[tuple] = None) -> None:
        """Execute a SQL statement."""
        if self.cursor is None:
            raise RuntimeError("Database not connected")
        self.cursor.execute(sql, params or ())
    
    def fetchall(self, sql: str, params: Optional[tuple] = None) -> List[tuple]:
        """Fetch all results from a query."""
        if self.cursor is None:
            raise RuntimeError("Database not connected")
        self.cursor.execute(sql, params or ())
        return self.cursor.fetchall()
    
    def fetchone(self, sql: str, params: Optional[tuple] = None) -> Optional[tuple]:
        """Fetch one result from a query."""
        if self.cursor is None:
            raise RuntimeError("Database not connected")
        self.cursor.execute(sql, params or ())
        return self.cursor.fetchone()
    
    def begin_transaction(self) -> None:
        """Begin a transaction."""
        self.execute("BEGIN TRANSACTION")
    
    def commit(self) -> None:
        """Commit the current transaction."""
        self.execute("COMMIT")
    
    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.execute("ROLLBACK")
    
    def close(self) -> None:
        """Close the database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()


class Migration(ABC):
    """Base class for migrations."""
    
    def __init__(self, version: str, name: str) -> None:
        """
        Initialize migration.
        
        Args:
            version: Migration version (e.g., "001", "002")
            name: Descriptive name of the migration
        """
        self.version = version
        self.name = name
    
    @abstractmethod
    def up(self, db: DatabaseAdapter) -> None:
        """
        Apply the migration.
        
        Args:
            db: Database adapter to execute migration
        """
        pass
    
    @abstractmethod
    def down(self, db: DatabaseAdapter) -> None:
        """
        Rollback the migration.
        
        Args:
            db: Database adapter to execute rollback
        """
        pass
    
    def get_checksum(self) -> str:
        """
        Calculate checksum of migration content.
        
        Returns:
            MD5 checksum of migration code
        """
        import inspect
        source = inspect.getsource(self.__class__)
        return hashlib.md5(source.encode()).hexdigest()


class SQLMigration(Migration):
    """Migration defined by SQL statements."""
    
    def __init__(
        self,
        version: str,
        name: str,
        up_sql: str,
        down_sql: str
    ) -> None:
        """
        Initialize SQL migration.
        
        Args:
            version: Migration version
            name: Descriptive name
            up_sql: SQL for applying migration
            down_sql: SQL for rolling back migration
        """
        super().__init__(version, name)
        self.up_sql = up_sql
        self.down_sql = down_sql
    
    def up(self, db: DatabaseAdapter) -> None:
        """Apply the migration."""
        for statement in self._split_statements(self.up_sql):
            if statement.strip():
                db.execute(statement)
    
    def down(self, db: DatabaseAdapter) -> None:
        """Rollback the migration."""
        for statement in self._split_statements(self.down_sql):
            if statement.strip():
                db.execute(statement)
    
    def get_checksum(self) -> str:
        """Calculate checksum of SQL content."""
        content = f"{self.up_sql}{self.down_sql}"
        return hashlib.md5(content.encode()).hexdigest()
    
    @staticmethod
    def _split_statements(sql: str) -> List[str]:
        """
        Split SQL script into individual statements.
        
        Args:
            sql: SQL script with multiple statements
            
        Returns:
            List of individual SQL statements
        """
        return [s.strip() for s in sql.split(';') if s.strip()]


class MigrationError(Exception):
    """Base exception for migration errors."""
    pass


class MigrationChecksumError(MigrationError):
    """Exception raised when migration checksum doesn't match."""
    pass


class MigrationNotFoundError(MigrationError):
    """Exception raised when migration is not found."""
    pass


class MigrationRegistry:
    """Registry to manage all migrations."""
    
    def __init__(self) -> None:
        """Initialize migration registry."""
        self.migrations: Dict[str, Migration] = {}
    
    def register(self, migration: Migration) -> None:
        """
        Register a migration.
        
        Args:
            migration: Migration to register
        """
        self.migrations[migration.version] = migration
        logger.debug(f"Registered migration {migration.version}: {migration.name}")
    
    def get(self, version: str) -> Migration:
        """
        Get migration by version.
        
        Args:
            version: Migration version
            
        Returns:
            Migration instance
            
        Raises:
            MigrationNotFoundError: If migration not found
        """
        if version not in self.migrations:
            raise MigrationNotFoundError(f"Migration {version} not found")
        return self.migrations[version]
    
    def get_all(self) -> List[Migration]:
        """
        Get all migrations sorted by version.
        
        Returns:
            List of migrations in order
        """
        return sorted(self.migrations.values(), key=lambda m: m.version)


class MigrationTracker:
    """Tracks applied migrations in the database."""
    
    SCHEMA_TABLE = "schema_migrations"
    
    def __init__(self, db: DatabaseAdapter) -> None:
        """
        Initialize migration tracker.
        
        Args:
            db: Database adapter
        """
        self.db = db
        self._ensure_schema_table()
    
    def _ensure_schema_table(self) -> None:
        """Create schema migrations table if it doesn't exist."""
        self.db.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.SCHEMA_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                checksum TEXT NOT NULL,
                applied_at TIMESTAMP NOT NULL,
                execution_time_ms INTEGER NOT NULL
            )
        """)
        logger.debug(f"Ensured {self.SCHEMA_TABLE} table exists")
    
    def is_applied(self, version: str) -> bool:
        """
        Check if migration is applied.
        
        Args:
            version: Migration version
            
        Returns:
            True if migration is applied, False otherwise
        """
        result = self.db.fetchone(
            f"SELECT version FROM {self.SCHEMA_TABLE} WHERE version = ?",
            (version,)
        )
        return result is not None
    
    def get_applied_migrations(self) -> List[MigrationRecord]:
        """
        Get all applied migrations.
        
        Returns:
            List of migration records
        """
        rows = self.db.fetchall(
            f"SELECT id, version, name, checksum, applied_at, execution_time_ms "
            f"FROM {self.SCHEMA_TABLE} ORDER BY version"
        )
        return [
            MigrationRecord(
                id=row[0],
                version=row[1],
                name=row[2],
                checksum=row[3],
                applied_at=datetime.fromisoformat(row[4]),
                execution_time_ms=row[5]
            )
            for row in rows
        ]
    
    def get_latest_version(self) -> Optional[str]:
        """
        Get the latest applied migration version.
        
        Returns:
            Latest version or None if no migrations applied
        """
        result = self.db.fetchone(
            f"SELECT version FROM {self.SCHEMA_TABLE} ORDER BY version DESC LIMIT 1"
        )
        return result[0] if result else None
    
    def record_migration(
        self,
        migration: Migration,
        execution_time_ms: int
    ) -> None:
        """
        Record a migration as applied.
        
        Args:
            migration: Migration that was applied
            execution_time_ms: Execution time in milliseconds
        """
        self.db.execute(
            f"INSERT INTO {self.SCHEMA_TABLE} "
            f"(version, name, checksum, applied_at, execution_time_ms) "
            f"VALUES (?, ?, ?, ?, ?)",
            (
                migration.version,
                migration.name,
                migration.get_checksum(),
                datetime.now().isoformat(),
                execution_time_ms
            )
        )
        logger.info(f"Recorded migration {migration.version} ({execution_time_ms}ms)")
    
    def remove_migration(self, version: str) -> None:
        """
        Remove a migration record.
        
        Args:
            version: Migration version to remove
        """
        self.db.execute(
            f"DELETE FROM {self.SCHEMA_TABLE} WHERE version = ?",
            (version,)
        )
        logger.info(f"Removed migration record {version}")
    
    def verify_checksum(self, migration: Migration) -> None:
        """
        Verify migration checksum matches recorded checksum.
        
        Args:
            migration: Migration to verify
            
        Raises:
            MigrationChecksumError: If checksums don't match
        """
        result = self.db.fetchone(
            f"SELECT checksum FROM {self.SCHEMA_TABLE} WHERE version = ?",
            (migration.version,)
        )
        
        if result:
            recorded_checksum = result[0]
            current_checksum = migration.get_checksum()
            
            if recorded_checksum != current_checksum:
                raise MigrationChecksumError(
                    f"Migration {migration.version} checksum mismatch. "
                    f"Expected: {recorded_checksum}, Got: {current_checksum}"
                )


class MigrationExecutor:
    """Executes migrations with transaction support and rollback."""
    
    def __init__(
        self,
        db: DatabaseAdapter,
        tracker: MigrationTracker
    ) -> None:
        """
        Initialize migration executor.
        
        Args:
            db: Database adapter
            tracker: Migration tracker
        """
        self.db = db
        self.tracker = tracker
    
    def execute_up(self, migration: Migration) -> None:
        """
        Execute migration up.
        
        Args:
            migration: Migration to execute
            
        Raises:
            MigrationError: If migration fails
        """
        logger.info(f"Applying migration {migration.version}: {migration.name}")
        
        start_time = datetime.now()
        
        try:
            self.db.begin_transaction()
            
            migration.up(self.db)
            
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self.tracker.record_migration(migration, execution_time_ms)
            
            self.db.commit()
            
            logger.info(
                f"Successfully applied migration {migration.version} "
                f"({execution_time_ms}ms)"
            )
            
        except Exception as e:
            logger.error(f"Failed to apply migration {migration.version}: {e}")
            self.db.rollback()
            raise MigrationError(f"Migration {migration.version} failed: {e}") from e
    
    def execute_down(self, migration: Migration) -> None:
        """
        Execute migration down.
        
        Args:
            migration: Migration to rollback
            
        Raises:
            MigrationError: If rollback fails
        """
        logger.info(f"Rolling back migration {migration.version}: {migration.name}")
        
        start_time = datetime.now()
        
        try:
            self.db.begin_transaction()
            
            migration.down(self.db)
            
            self.tracker.remove_migration(migration.version)
            
            self.db.commit()
            
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.info(
                f"Successfully rolled back migration {migration.version} "
                f"({execution_time_ms}ms)"
            )
            
        except Exception as e:
            logger.error(f"Failed to rollback migration {migration.version}: {e}")
            self.db.rollback()
            raise MigrationError(
                f"Migration {migration.version} rollback failed: {e}"
            ) from e


class MigrationManager:
    """Main migration manager coordinating all components."""
    
    def __init__(
        self,
        db: DatabaseAdapter,
        registry: MigrationRegistry
    ) -> None:
        """
        Initialize migration manager.
        
        Args:
            db: Database adapter
            registry: Migration registry
        """
        self.db = db
        self.registry = registry
        self.tracker = MigrationTracker(db)
        self.executor = MigrationExecutor(db, self.tracker)
    
    def migrate_up(self, target_version: Optional[str] = None) -> None:
        """
        Apply