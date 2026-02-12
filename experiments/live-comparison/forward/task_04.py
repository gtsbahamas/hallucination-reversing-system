import hashlib
import json
import logging
import os
import sqlite3
import sys
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Type, NamedTuple

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


class ConnectionError(Exception):
    """Exception raised for database connection errors."""
    pass


class SQLiteAdapter:
    """SQLite implementation of DatabaseAdapter."""
    
    def __init__(self, database_path: str, max_retries: int = 3, retry_delay: float = 1.0) -> None:
        """
        Initialize SQLite adapter.
        
        Args:
            database_path: Path to SQLite database file
            max_retries: Maximum number of connection retry attempts
            retry_delay: Initial delay between retries in seconds
        """
        self.database_path = self._validate_database_path(database_path)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self._lock = threading.Lock()
        self._connect()
    
    def _validate_database_path(self, database_path: str) -> str:
        """
        Validate and normalize database path.
        
        Args:
            database_path: Path to validate
            
        Returns:
            Absolute validated path
            
        Raises:
            ValueError: If path is invalid
        """
        if not database_path:
            raise ValueError("Database path cannot be empty")
        
        path = Path(database_path).resolve()
        
        if path.exists() and not path.is_file():
            raise ValueError(f"Database path exists but is not a file: {path}")
        
        parent_dir = path.parent
        if not parent_dir.exists():
            raise ValueError(f"Parent directory does not exist: {parent_dir}")
        
        if parent_dir.exists() and not os.access(parent_dir, os.W_OK):
            raise ValueError(f"Parent directory is not writable: {parent_dir}")
        
        return str(path)
    
    def _connect(self) -> None:
        """Establish database connection with retry logic."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                self.connection = sqlite3.connect(
                    self.database_path,
                    timeout=30.0,
                    check_same_thread=False
                )
                self.cursor = self.connection.cursor()
                self.cursor.execute("PRAGMA journal_mode=WAL")
                logger.debug(f"Connected to database: {self.database_path}")
                return
            except sqlite3.Error as e:
                last_error = e
                logger.warning(
                    f"Connection attempt {attempt + 1}/{self.max_retries} failed: {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
        
        raise ConnectionError(
            f"Failed to connect to database after {self.max_retries} attempts: {last_error}"
        )
    
    def _ensure_connected(self) -> None:
        """Ensure database connection is active."""
        if self.connection is None or self.cursor is None:
            raise ConnectionError("Database connection is not established")
        
        try:
            self.cursor.execute("SELECT 1")
        except sqlite3.Error:
            logger.warning("Connection lost, attempting to reconnect...")
            self._connect()
    
    def execute(self, sql: str, params: Optional[tuple] = None) -> None:
        """Execute a SQL statement."""
        with self._lock:
            self._ensure_connected()
            try:
                self.cursor.execute(sql, params or ())
            except sqlite3.Error as e:
                raise RuntimeError(f"Failed to execute SQL: {e}") from e
    
    def fetchall(self, sql: str, params: Optional[tuple] = None) -> List[tuple]:
        """Fetch all results from a query."""
        with self._lock:
            self._ensure_connected()
            try:
                self.cursor.execute(sql, params or ())
                return self.cursor.fetchall()
            except sqlite3.Error as e:
                raise RuntimeError(f"Failed to fetch results: {e}") from e
    
    def fetchone(self, sql: str, params: Optional[tuple] = None) -> Optional[tuple]:
        """Fetch one result from a query."""
        with self._lock:
            self._ensure_connected()
            try:
                self.cursor.execute(sql, params or ())
                return self.cursor.fetchone()
            except sqlite3.Error as e:
                raise RuntimeError(f"Failed to fetch result: {e}") from e
    
    def begin_transaction(self) -> None:
        """Begin a transaction."""
        with self._lock:
            self._ensure_connected()
            try:
                self.cursor.execute("BEGIN IMMEDIATE")
            except sqlite3.Error as e:
                raise RuntimeError(f"Failed to begin transaction: {e}") from e
    
    def commit(self) -> None:
        """Commit the current transaction."""
        with self._lock:
            self._ensure_connected()
            try:
                self.connection.commit()
            except sqlite3.Error as e:
                raise RuntimeError(f"Failed to commit transaction: {e}") from e
    
    def rollback(self) -> None:
        """Rollback the current transaction."""
        with self._lock:
            self._ensure_connected()
            try:
                self.connection.rollback()
            except sqlite3.Error as e:
                raise RuntimeError(f"Failed to rollback transaction: {e}") from e
    
    def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            if self.cursor:
                try:
                    self.cursor.close()
                except sqlite3.Error:
                    pass
                self.cursor = None
            if self.connection:
                try:
                    self.connection.close()
                except sqlite3.Error:
                    pass
                self.connection = None
                logger.debug("Database connection closed")


class Migration(ABC):
    """Base class for migrations."""
    
    def __init__(self, version: str, name: str) -> None:
        """
        Initialize migration.
        
        Args:
            version: Migration version (e.g., "001", "002")
            name: Descriptive name of the migration
        """
        self._validate_version(version)
        self.version = version
        self.name = name
    
    @staticmethod
    def _validate_version(version: str) -> None:
        """
        Validate migration version format.
        
        Args:
            version: Version string to validate
            
        Raises:
            ValueError: If version format is invalid
        """
        if not version:
            raise ValueError("Migration version cannot be empty")
        
        if not version.isdigit():
            raise ValueError(
                f"Migration version must be numeric: {version}. "
                f"Use zero-padded format like '001', '002', etc."
            )
        
        if len(version) < 3:
            raise ValueError(
                f"Migration version should be zero-padded (e.g., '001' not '{version}')"
            )
    
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
            SHA-256 checksum of migration code
        """
        import inspect
        source = inspect.getsource(self.__class__)
        return hashlib.sha256(source.encode()).hexdigest()


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
        
        if not up_sql or not up_sql.strip():
            raise ValueError("up_sql cannot be empty")
        
        if not down_sql or not down_sql.strip():
            raise ValueError(
                "down_sql cannot be empty. If migration is irreversible, "
                "explicitly provide a comment or raise an error in down()"
            )
        
        self.up_sql = up_sql
        self.down_sql = down_sql
    
    def up(self, db: DatabaseAdapter) -> None:
        """Apply the migration."""
        for statement in self._parse_sql_statements(self.up_sql):
            if statement.strip():
                db.execute(statement)
    
    def down(self, db: DatabaseAdapter) -> None:
        """Rollback the migration."""
        for statement in self._parse_sql_statements(self.down_sql):
            if statement.strip():
                db.execute(statement)
    
    def get_checksum(self) -> str:
        """Calculate checksum of SQL content."""
        content = f"{self.up_sql}{self.down_sql}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    @staticmethod
    def _parse_sql_statements(sql: str) -> List[str]:
        """
        Parse SQL script into individual statements.
        
        Handles strings, comments, and semicolons within statements.
        
        Args:
            sql: SQL script with multiple statements
            
        Returns:
            List of individual SQL statements
        """
        statements = []
        current_statement = []
        in_string = False
        in_single_line_comment = False
        in_multi_line_comment = False
        string_char = None
        i = 0
        
        while i < len(sql):
            char = sql[i]
            
            if in_single_line_comment:
                current_statement.append(char)
                if char == '\n':
                    in_single_line_comment = False
                i += 1
                continue
            
            if in_multi_line_comment:
                current_statement.append(char)
                if char == '*' and i + 1 < len(sql) and sql[i + 1] == '/':
                    current_statement.append('/')
                    in_multi_line_comment = False
                    i += 2
                    continue
                i += 1
                continue
            
            if not in_string:
                if char == '-' and i + 1 < len(sql) and sql[i + 1] == '-':
                    in_single_line_comment = True
                    current_statement.append(char)
                    i += 1
                    continue
                
                if char == '/' and i + 1 < len(sql) and sql[i + 1] == '*':
                    in_multi_line_comment = True
                    current_statement.append(char)
                    i += 1
                    continue
                
                if char in ('"', "'"):
                    in_string = True
                    string_char = char
                    current_statement.append(char)
                    i += 1
                    continue
                
                if char == ';':
                    statement = ''.join(current_statement).strip()
                    if statement:
                        statements.append(statement)
                    current_statement = []
                    i += 1
                    continue
            
            else:
                if char == string_char:
                    if i + 1 < len(sql) and sql[i + 1] == string_char:
                        current_statement.append(char)
                        current_statement.append(char)
                        i += 2
                        continue
                    else:
                        in_string = False
                        string_char = None
            
            current_statement.append(char)
            i += 1
        
        final_statement = ''.join(current_statement).strip()
        if final_statement:
            statements.append(final_statement)
        
        return statements


class MigrationError(Exception):
    """Base exception for migration errors."""
    pass


class MigrationChecksumError(MigrationError):
    """Exception raised when migration checksum doesn't match."""
    pass


class MigrationNotFoundError(MigrationError):
    """Exception raised when migration is not found."""
    pass


class MigrationLockError(MigrationError):
    """Exception raised when migration lock cannot be acquired."""
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
            
        Raises:
            ValueError: If migration with same version already registered
        """
        if migration.version in self.migrations:
            raise ValueError(
                f"Migration {migration.version} is already registered"
            )
        
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
    LOCK_TABLE = "schema_migrations_lock"
    
    def __init__(self, db: DatabaseAdapter) -> None:
        """
        Initialize migration tracker.
        
        Args:
            db: Database adapter
        """
        self.db = db
        self._ensure_schema_table()
        self._ensure_lock_table()
    
    def _ensure_schema_table(self) -> None:
        """Create schema migrations table if it doesn't exist."""
        self.db.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.SCHEMA_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                checksum TEXT NOT NULL,
                applied_at TEXT NOT NULL,
                execution_time_ms INTEGER NOT NULL
            )
        """)
        logger.debug(f"Ensured {self.SCHEMA_TABLE} table exists")
    
    def _ensure_lock_table(self) -> None:
        """Create migration lock table if it doesn't exist."""
        self.db.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.LOCK_TABLE} (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                locked INTEGER NOT NULL DEFAULT 0,
                locked_at TEXT,
                locked_by TEXT
            )
        """)
        self.db.execute(f"""
            INSERT OR IGNORE INTO {self.LOCK_TABLE} (id, locked) VALUES (1, 0)
        """)
        logger.debug(f"Ensured {self.LOCK_TABLE} table exists")
    
    def acquire_lock(self, timeout: float = 300.0) -> None:
        """
        Acquire migration lock.
        
        Args:
            timeout: Maximum time to wait for lock in seconds
            
        Raises:
            MigrationLockError: If lock cannot be acquired
        """
        start_time = time.time()
        lock_id = f"{os.getpid()}_{threading.current_thread().ident}"
        
        while time.time() - start_time < timeout:
            try:
                self.db.begin_transaction()
                
                result = self.db.fetchone(
                    f"SELECT locked, locked_at, locked_by FROM {self.LOCK_TABLE} WHERE id = 1"
                )
                
                if result and result[0] == 0:
                    self.db.execute(
                        f"UPDATE {self.LOCK_TABLE} SET locked = 1, locked_at = ?, locked_by = ? WHERE id = 1",
                        (datetime.now().isoformat(), lock_id)
                    )
                    self.db.commit()
                    logger.info(f"Acquired migration lock: {lock_id}")
                    return
                
                self.db.rollback()
                
                if result:
                    locked_at = result[1]
                    locked_by = result[2]
                    logger.debug(
                        f"Migration lock held by {locked_by} since {locked_at}, waiting..."
                    )
                
                time.sleep(1.0)
                
            except Exception as e:
                self.db.rollback()
                raise MigrationLockError(f"Failed to acquire lock: {e}") from e
        
        raise MigrationLockError(
            f"Failed to acquire migration lock within {timeout} seconds"
        )
    
    def release_lock(self) -> None:
        """Release migration lock."""
        try:
            self.db.begin_transaction()
            self.db.execute(
                f"UPDATE {self.LOCK_TABLE} SET locked = 0, locked_at = NULL, locked_by = NULL WHERE id = 1"
            )
            self.db.commit()
            logger.info("Released migration lock")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to release lock: {e}")
            raise
    
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
                    f"Expected: {recorded_checksum}, Got: {current_checksum}. "
                    f"Applied migration has been modified!"
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
            try:
                self.db.rollback()
                logger.info(f"Rolled back failed migration {migration.version}")
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {rollback_error}")
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
            try:
                self.db.rollback()
                logger.info(f"Rolled back failed rollback attempt for {migration.version}")
            except Exception as rollback_error:
                logger.error(f"Rollback of rollback failed: {rollback_error}")
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
    
    def __enter__(self) -> 'MigrationManager':
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
    
    def close(self) -> None:
        """Close database connection."""
        self.db.close()
    
    def migrate_up(
        self,
        target_version: Optional[str] = None,
        dry_run: bool = False
    ) -> None:
        """
        Apply pending migrations up to target version.
        
        Args:
            target_version: Version to migrate to (None for latest)
            dry_run: If True, only log planned migrations without executing
            
        Raises:
            MigrationError: If migration fails
        """
        try:
            self.tracker.acquire_lock()
            
            all_migrations = self.registry.get_all()
            applied_records = self.tracker.get_applied_migrations()
            applied_versions = {record.version for record in applied_records}
            
            for record in applied_records:
                try:
                    migration = self.registry.get(record.version)
                    self.tracker.verify_checksum(migration)
                except MigrationNotFoundError:
                    logger.warning(
                        f"Applied migration {record.version} not found in registry"
                    )
                except MigrationChecksumError as e:
                    logger.error(str(e))
                    raise
            
            pending_migrations = [
                m for m in all_migrations
                if m.version not in applied_versions
            ]
            
            if target_version:
                pending_migrations = [
                    m for m in pending_migrations
                    if m.version <= target_version
                ]
            
            if not pending_migrations:
                logger.info("No pending migrations to apply")
                return
            
            logger.info(f"Found {len(pending_migrations)} pending migration(s)")
            
            if dry_run:
                logger.info("DRY RUN MODE - No migrations will be applied")
                for migration in pending_migrations:
                    logger.info(
                        f"Would apply: {migration.version} - {migration.name}"
                    )
                return
            
            for migration in pending_migrations:
                self.executor.execute_up(migration)
            
            logger.info("All migrations applied successfully")
            
        finally:
            try:
                self.tracker.release_lock()
            except Exception as e:
                logger.error(f"Failed to release lock: {e}")
    
    def migrate_down(
        self,
        target_version: Optional[str] = None,
        steps: int = 1
    ) -> None:
        """
        Rollback migrations.
        
        Args:
            target_version: Version to rollback to (None to use steps)
            steps: Number of migrations to rollback (ignored if target_version set)
            
        Raises:
            MigrationError: If rollback fails
        """
        try:
            self.tracker.acquire_lock()
            
            applied_records = self.tracker.get_applied_migrations()
            
            if not applied_records:
                logger.info("No migrations to rollback")
                return
            
            applied_records.reverse()
            
            migrations_to_rollback = []
            
            if target_version:
                for record in applied_records:
                    if record.version > target_version:
                        migrations_to_rollback.append(record.version)
                    else:
                        break
            else:
                migrations_to_rollback = [
                    record.version for record in applied_records[:steps]
                ]
            
            if not migrations_to_rollback:
                logger.info("No migrations to rollback")
                return
            
            logger.info(f"Rolling back {len(migrations_to_rollback)} migration(s)")
            
            for version in migrations_to_rollback:
                migration = self.registry.get(version)
                self.executor.execute_down(migration)
            
            logger.info("Rollback completed successfully")
            
        finally:
            try:
                self.tracker.release_lock()
            except Exception as e:
                logger.error(f"Failed to release lock: {e}")
    
    def status(self) -> Dict[str, Any]:
        """
        Get migration status.
        
        Returns:
            Dictionary with migration status information
        """
        all_migrations = self.registry.get_all()
        applied_records = self.tracker.get_applied_migrations()
        applied_versions = {record.version for record in applied_records}
        
        pending = [m for m in all_migrations if m.version not in applied_versions]
        
        return {