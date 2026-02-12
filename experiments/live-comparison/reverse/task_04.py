import os
import re
import ast
import logging
import importlib.util
import sqlite3
import signal
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass
from enum import Enum


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MigrationStatus(Enum):
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"


class MigrationError(Exception):
    def __init__(
        self,
        message: str,
        migration_version: Optional[str] = None,
        error_type: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        partial_changes_rolled_back: bool = False
    ):
        super().__init__(message)
        self.migration_version = migration_version
        self.error_type = error_type
        self.original_exception = original_exception
        self.partial_changes_rolled_back = partial_changes_rolled_back


class ValidationError(MigrationError):
    pass


class DuplicateVersionError(MigrationError):
    pass


class ConcurrentMigrationError(MigrationError):
    pass


class SecurityError(MigrationError):
    pass


class TimeoutError(MigrationError):
    pass


@dataclass
class MigrationResult:
    success: bool
    applied: List[str]
    failed: Optional[str] = None
    error: Optional[Exception] = None


@dataclass
class AppliedMigration:
    version: str
    applied_at: str


class Migration(ABC):
    @abstractmethod
    def up(self, connection: sqlite3.Connection) -> None:
        pass

    @abstractmethod
    def down(self, connection: sqlite3.Connection) -> None:
        pass


MIGRATIONS_TABLE = "schema_migrations"
MIGRATION_FILENAME_PATTERN = r"^\d{3,}_[a-z0-9_]+\.py$"
MIGRATION_LOCK_ID = 987654321


class MigrationSystem:
    def __init__(self, migrations_dir: str, db_path: str):
        self.migrations_dir = Path(migrations_dir)
        self.db_path = db_path
        self._cached_migrations: Optional[List[str]] = None
        self._initialize_tracking_table()

    def _initialize_tracking_table(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {MIGRATIONS_TABLE} (
                    version TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    applied_at TEXT,
                    error TEXT
                )
            """)
            conn.commit()

    def _acquire_lock(self, connection: sqlite3.Connection) -> None:
        try:
            connection.execute("BEGIN EXCLUSIVE")
        except sqlite3.OperationalError as e:
            raise ConcurrentMigrationError(
                "Another migration is currently in progress"
            ) from e

    def _release_lock(self, connection: sqlite3.Connection) -> None:
        try:
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    def _validate_path(self, path: str) -> None:
        path_obj = Path(path)
        
        if ".." in path_obj.parts:
            raise SecurityError("Path traversal detected")
        
        if path_obj.is_absolute():
            raise SecurityError("Absolute paths not allowed")
        
        try:
            resolved = (self.migrations_dir / path_obj).resolve()
            if not str(resolved).startswith(str(self.migrations_dir.resolve())):
                raise SecurityError("Path escapes migrations directory")
        except Exception as e:
            raise SecurityError(f"Invalid path: {e}") from e

    def _validate_filename(self, filename: str) -> None:
        try:
            filename.encode("ascii")
        except UnicodeEncodeError:
            raise ValidationError(f"Non-ASCII filename not supported: {filename}")
        
        if not re.match(MIGRATION_FILENAME_PATTERN, filename):
            raise ValidationError(f"Invalid migration name: {filename}")

    def _extract_version(self, filename: str) -> str:
        return filename.split("_")[0]

    def _validate_syntax(self, filepath: Path) -> None:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            ast.parse(content)
        except SyntaxError as e:
            raise MigrationError(
                f"Syntax error in {filepath.name}: {e}",
                error_type="SyntaxError",
                original_exception=e
            ) from e

    def _validate_migration_class(self, filepath: Path) -> None:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        tree = ast.parse(content)
        has_class = any(isinstance(node, ast.ClassDef) for node in tree.body)
        
        if not has_class:
            raise ValidationError(f"No migration class found in {filepath.name}")

    def _discover_migrations(self, refresh: bool = False) -> List[str]:
        if self._cached_migrations is not None and not refresh:
            return self._cached_migrations
        
        if not self.migrations_dir.exists():
            self._cached_migrations = []
            return []
        
        migration_files = []
        for filepath in self.migrations_dir.glob("*.py"):
            filename = filepath.name
            
            if filename.startswith("__"):
                continue
            
            try:
                self._validate_filename(filename)
                self._validate_syntax(filepath)
                self._validate_migration_class(filepath)
                migration_files.append(filename)
            except ValidationError:
                raise
        
        versions = [self._extract_version(f) for f in migration_files]
        if len(versions) != len(set(versions)):
            version_files = {}
            for f in migration_files:
                v = self._extract_version(f)
                if v not in version_files:
                    version_files[v] = []
                version_files[v].append(f)
            
            duplicates = [files for files in version_files.values() if len(files) > 1]
            raise DuplicateVersionError(
                f"Duplicate migration versions found: {duplicates}"
            )
        
        migration_files.sort(key=lambda m: int(self._extract_version(m)))
        self._cached_migrations = migration_files
        return migration_files

    def _load_migration(self, filename: str) -> Migration:
        self._validate_path(filename)
        filepath = self.migrations_dir / filename
        
        module_name = filename[:-3]
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        if spec is None or spec.loader is None:
            raise MigrationError(f"Could not load migration: {filename}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        migration_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, Migration) and 
                attr is not Migration):
                migration_class = attr
                break
        
        if migration_class is None:
            raise ValidationError(f"No Migration class found in {filename}")
        
        migration_instance = migration_class()
        
        if not hasattr(migration_instance, "up") or not callable(migration_instance.up):
            raise MigrationError(f"{filename} missing required method: up()")
        
        if not hasattr(migration_instance, "down") or not callable(migration_instance.down):
            raise MigrationError(f"{filename} missing required method: down()")
        
        return migration_instance

    def _get_applied_migrations_from_db(self) -> Set[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"SELECT version FROM {MIGRATIONS_TABLE} WHERE status = ?",
                (MigrationStatus.APPLIED.value,)
            )
            return {row[0] for row in cursor.fetchall()}

    def _track_migration(
        self,
        connection: sqlite3.Connection,
        version: str,
        status: MigrationStatus,
        error: Optional[str] = None
    ) -> None:
        applied_at = datetime.utcnow().isoformat() + "Z" if status == MigrationStatus.APPLIED else None
        
        connection.execute(
            f"""
            INSERT OR REPLACE INTO {MIGRATIONS_TABLE} 
            (version, status, applied_at, error)
            VALUES (?, ?, ?, ?)
            """,
            (version, status.value, applied_at, error)
        )

    def _remove_tracking(self, connection: sqlite3.Connection, version: str) -> None:
        connection.execute(
            f"DELETE FROM {MIGRATIONS_TABLE} WHERE version = ?",
            (version,)
        )

    def _execute_with_timeout(
        self,
        func: Any,
        connection: sqlite3.Connection,
        timeout: Optional[int] = None
    ) -> None:
        if timeout is None:
            func(connection)
            return
        
        def timeout_handler(signum: int, frame: Any) -> None:
            raise TimeoutError(f"Migration exceeded timeout of {timeout} seconds")
        
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        try:
            func(connection)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    def migrate_up(
        self,
        dry_run: bool = False,
        timeout: Optional[int] = None
    ) -> MigrationResult:
        try:
            migration_files = self._discover_migrations()
        except Exception as e:
            return MigrationResult(success=False, applied=[], error=e)
        
        if not migration_files:
            return MigrationResult(success=True, applied=[])
        
        applied_versions = self._get_applied_migrations_from_db()
        pending = [
            f for f in migration_files
            if self._extract_version(f) not in applied_versions
        ]
        
        if not pending:
            return MigrationResult(success=True, applied=[])
        
        if dry_run:
            planned = []
            for filename in pending:
                version = self._extract_version(filename)
                logger.info(f"Would apply: {version}", extra={
                    "timestamp": datetime.utcnow().isoformat()
                })
                planned.append(version)
            return MigrationResult(success=True, applied=planned)
        
        applied = []
        connection = None
        
        try:
            connection = sqlite3.connect(self.db_path)
            connection.isolation_level = None
            self._acquire_lock(connection)
            
            for filename in pending:
                version = self._extract_version(filename)
                
                logger.info(f"Started migration {version}", extra={
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                migration = self._load_migration(filename)
                
                connection.execute("BEGIN")
                
                try:
                    self._execute_with_timeout(migration.up, connection, timeout)
                    self._track_migration(connection, version, MigrationStatus.APPLIED)
                    connection.commit()
                    
                    applied.append(version)
                    
                    logger.info(f"Completed migration {version}", extra={
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                except Exception as e1:
                    connection.rollback()
                    
                    logger.error(f"Migration {version} failed: {e1}", extra={
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    rollback_successful = False
                    try:
                        connection.execute("BEGIN")
                        migration.down(connection)
                        connection.commit()
                        rollback_successful = True
                        logger.info(f"Rolled back migration {version}")
                    except Exception as e2:
                        connection.rollback()
                        logger.error(f"Rollback of {version} also failed: {e2}")
                        self._track_migration(
                            connection,
                            version,
                            MigrationStatus.FAILED,
                            f"Migration error: {str(e1)}; Rollback error: {str(e2)}"
                        )
                        connection.commit()
                    
                    raise MigrationError(
                        f"Migration {version} failed",
                        migration_version=version,
                        error_type=type(e1).__name__,
                        original_exception=e1,
                        partial_changes_rolled_back=rollback_successful
                    ) from e1
                finally:
                    del migration
            
            return MigrationResult(success=True, applied=applied)
            
        except Exception as e:
            return MigrationResult(success=False, applied=applied, error=e)
        finally:
            if connection:
                try:
                    self._release_lock(connection)
                except Exception:
                    pass
                connection.close()

    def migrate_down(self, count: int = 1) -> MigrationResult:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"""
                SELECT version FROM {MIGRATIONS_TABLE}
                WHERE status = ?
                ORDER BY applied_at DESC
                """,
                (MigrationStatus.APPLIED.value,)
            )
            applied_versions = [row[0] for row in cursor.fetchall()]
        
        if count > len(applied_versions):
            raise ValueError(
                f"Cannot rollback {count} migrations, only {len(applied_versions)} applied"
            )
        
        to_rollback = applied_versions[:count]
        rolled_back = []
        connection = None
        
        try:
            connection = sqlite3.connect(self.db_path)
            connection.isolation_level = None
            self._acquire_lock(connection)
            
            for version in to_rollback:
                migration_files = self._discover_migrations()
                filename = None
                for f in migration_files:
                    if self._extract_version(f) == version:
                        filename = f
                        break
                
                if filename is None:
                    raise MigrationError(f"Migration file for version {version} not found")
                
                logger.info(f"Rolling back migration {version}", extra={
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                migration = self._load_migration(filename)
                
                connection.execute("BEGIN")
                
                try:
                    migration.down(connection)
                    self._remove_tracking(connection, version)
                    connection.commit()
                    
                    rolled_back.append(version)
                    
                    logger.info(f"Rolled back migration {version}", extra={
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                except Exception as e:
                    connection.rollback()
                    logger.error(f"Rollback of {version} failed: {e}")
                    
                    raise MigrationError(
                        f"Rollback of {version} failed",
                        migration_version=version,
                        error_type=type(e).__name__,
                        original_exception=e,
                        partial_changes_rolled_back=False
                    ) from e
                finally:
                    del migration
            
            return MigrationResult(success=True, applied=rolled_back)
            
        except Exception as e:
            return MigrationResult(success=False, applied=rolled_back, error=e)
        finally:
            if connection:
                try:
                    self._release_lock(connection)
                except Exception:
                    pass
                connection.close()

    def migrate_to(self, target_version: str) -> MigrationResult:
        migration_files = self._discover_migrations()
        all_versions = [self._extract_version(f) for f in migration_files]
        
        if target_version not in all_versions:
            raise ValueError(f"Target version {target_version} not found")
        
        applied_versions = list(self._get_applied_migrations_from_db())
        current_version = applied_versions[-1] if applied_versions else None
        
        target_idx = all_versions.index(target_version)
        current_idx = all_versions.index(current_version) if current_version else -1
        
        if target_idx > current_idx:
            pending = migration_files[current_idx + 1:target_idx + 1]
            applied = []
            connection = None
            
            try:
                connection = sqlite3.connect(self.db_path)
                connection.isolation_level = None
                self._acquire_lock(connection)
                
                for filename in pending:
                    version = self._extract_version(filename)
                    migration = self._load_migration(filename)
                    
                    connection.execute("BEGIN")
                    
                    try:
                        migration.up(connection)
                        self._track_migration(connection, version, MigrationStatus.APPLIED)
                        connection.commit()
                        applied.append(version)
                        
                    except Exception as e:
                        connection.rollback()
                        try:
                            connection.execute("BEGIN")
                            migration.down(connection)
                            connection.commit()
                        except Exception:
                            connection.rollback()
                        
                        raise MigrationError(
                            f"Migration {version} failed",
                            migration_version=version,
                            error_type=type(e).__name__,
                            original_exception=e,
                            partial_changes_rolled_back=True
                        ) from e
                    finally:
                        del migration
                
                return MigrationResult(success=True, applied=applied)
                
            finally:
                if connection:
                    try:
                        self._release_lock(connection)
                    except Exception:
                        pass
                    connection.close()
        
        elif target_idx < current_idx:
            to_rollback_count = current_idx - target_idx
            return self.migrate_down(to_rollback_count)
        
        else:
            return MigrationResult(success=True, applied=[])

    def get_applied_migrations(self) -> List[AppliedMigration]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"""
                SELECT version, applied_at FROM {MIGRATIONS_TABLE}
                WHERE status = ?
                ORDER BY applied_at
                """,
                (MigrationStatus.APPLIED.value,)
            )
            return [
                AppliedMigration(version=row[0], applied_at=row[1])
                for row in cursor.fetchall()
            ]

    def get_migration_status(self) -> Dict[str, List[str]]:
        migration_files = self._discover_migrations()
        all_versions = {self._extract_version(f) for f in migration_files}
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"SELECT version, status FROM {MIGRATIONS_TABLE}"
            )
            tracked = {row[0]: row[1] for row in cursor.fetchall()}
        
        applied = [v for v, s in tracked.items() if s == MigrationStatus.APPLIED.value]
        failed = [v for v, s in tracked.items() if s == MigrationStatus.FAILED.value]
        pending = [v for v in all_versions if v not in tracked]
        
        return {
            "pending": sorted(pending, key=int),
            "applied": sorted(applied, key=int),
            "failed": sorted(failed, key=int)
        }

    def get_pending_migrations(self, refresh: bool = False) -> List[str]:
        migration_files = self._discover_migrations(refresh=refresh)
        applied_versions = self._get_applied_migrations_from_db()
        
        return [
            self._extract_version(f)
            for f in migration_files
            if self._extract_version(f) not in applied_versions
        ]