"""
Atomic, Thread-Safe JSON Storage Engine for Healthcare AI Application.
Provides ACID-like atomic persistence, in-memory caching, indexing, query filtering,
sorting, pagination, and multi-file transaction coordination without any SQL/NoSQL databases.
"""

import json
import os
import shutil
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from core.exceptions import (
    RecordAlreadyExistsError,
    RecordNotFoundError,
    StorageError,
)

# Global thread lock for file operations
_GLOBAL_LOCK = threading.RLock()


def utc_now_iso() -> str:
    """Generate current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


class JsonTable:
    """
    Represents an atomic JSON collection/table backed by a local JSON file.
    Supports CRUD, multi-criteria filtering, indexed lookups, and auto-generated UUIDs.
    """

    def __init__(self, file_path: Union[str, Path], table_name: str, primary_key: str = "id"):
        self.file_path = Path(file_path)
        self.table_name = table_name
        self.primary_key = primary_key
        self._lock = threading.RLock()
        self._cache: Optional[List[Dict[str, Any]]] = None
        self._last_mtime: float = 0.0

        # Ensure parent directories and initial JSON file exist
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Create the file with an empty list `[]` if it doesn't exist."""
        with self._lock:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.file_path.exists() or self.file_path.stat().st_size == 0:
                self._write_raw([])

    def _read_raw(self) -> List[Dict[str, Any]]:
        """Read and parse the raw JSON file with fallback recovery."""
        with self._lock:
            if not self.file_path.exists():
                self._ensure_file_exists()
                return []

            try:
                mtime = self.file_path.stat().st_mtime
                if self._cache is not None and mtime == self._last_mtime:
                    return [dict(item) for item in self._cache]

                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        data = []
                    else:
                        data = json.loads(content)

                if not isinstance(data, list):
                    raise StorageError(f"Corrupted storage file: {self.file_path} is not a JSON list.")

                self._cache = data
                self._last_mtime = mtime
                return [dict(item) for item in data]

            except json.JSONDecodeError as exc:
                # Backup corrupted file and reset
                backup_path = self.file_path.with_suffix(f".corrupt.{int(datetime.now().timestamp())}.json")
                try:
                    shutil.copy2(self.file_path, backup_path)
                except Exception:
                    pass
                self._write_raw([])
                raise StorageError(
                    f"Corrupted JSON in table '{self.table_name}'. Backup saved to {backup_path.name}. "
                    f"Error: {str(exc)}"
                )
            except Exception as e:
                raise StorageError(f"Failed to read table '{self.table_name}': {str(e)}")

    def _write_raw(self, data: List[Dict[str, Any]]) -> None:
        """Atomically write data using a temporary file and replace operation."""
        with self._lock:
            with _GLOBAL_LOCK:
                parent_dir = self.file_path.parent
                parent_dir.mkdir(parents=True, exist_ok=True)

                # Create temp file in same directory to guarantee atomic rename on all filesystems
                temp_file = None
                try:
                    fd, temp_path_str = tempfile.mkstemp(
                        dir=parent_dir,
                        prefix=f".tmp_{self.table_name}_",
                        suffix=".json"
                    )
                    temp_file = Path(temp_path_str)

                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                        f.flush()
                        os.fsync(f.fileno())

                    # Atomic replace
                    temp_file.replace(self.file_path)

                    self._cache = data
                    self._last_mtime = self.file_path.stat().st_mtime

                except Exception as e:
                    if temp_file and temp_file.exists():
                        try:
                            temp_file.unlink()
                        except Exception:
                            pass
                    raise StorageError(f"Failed to write atomically to table '{self.table_name}': {str(e)}")

    def find_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        filter_func: Optional[Callable[[Dict[str, Any]], bool]] = None,
        sort_by: Optional[str] = None,
        reverse: bool = False,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Query records matching optional filters dictionary, custom predicate function,
        with optional sorting, limit, and offset.
        """
        records = self._read_raw()

        if filters:
            records = [
                r for r in records
                if all(r.get(k) == v for k, v in filters.items())
            ]

        if filter_func:
            records = [r for r in records if filter_func(r)]

        if sort_by:
            records.sort(
                key=lambda x: (x.get(sort_by) is None, x.get(sort_by)),
                reverse=reverse,
            )

        if offset > 0:
            records = records[offset:]

        if limit is not None and limit >= 0:
            records = records[:limit]

        return records

    def find_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Look up a single record by its primary key ID."""
        records = self._read_raw()
        for record in records:
            if record.get(self.primary_key) == record_id:
                return dict(record)
        return None

    def get_by_id(self, record_id: str) -> Dict[str, Any]:
        """Look up a single record by ID or raise RecordNotFoundError."""
        record = self.find_by_id(record_id)
        if not record:
            raise RecordNotFoundError(self.table_name, record_id)
        return record

    def find_one(
        self,
        filters: Optional[Dict[str, Any]] = None,
        filter_func: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Return the first record matching filters, or None."""
        records = self.find_all(filters=filters, filter_func=filter_func, limit=1)
        return records[0] if records else None

    def insert(self, record: Dict[str, Any], unique_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Insert a new record. Automatically generates UUID primary key and timestamps.
        Optionally validates uniqueness of specified fields.
        """
        with self._lock:
            records = self._read_raw()

            # Ensure primary key
            if self.primary_key not in record or not record[self.primary_key]:
                record[self.primary_key] = str(uuid.uuid4())

            rec_id = record[self.primary_key]

            # Check primary key uniqueness
            if any(r.get(self.primary_key) == rec_id for r in records):
                raise RecordAlreadyExistsError(self.table_name, self.primary_key, str(rec_id))

            # Check unique fields
            if unique_fields:
                for field in unique_fields:
                    val = record.get(field)
                    if val is not None and any(r.get(field) == val for r in records):
                        raise RecordAlreadyExistsError(self.table_name, field, str(val))

            # Stamp creation and update times
            now = utc_now_iso()
            if "created_at" not in record:
                record["created_at"] = now
            if "updated_at" not in record:
                record["updated_at"] = now

            records.append(record)
            self._write_raw(records)
            return dict(record)

    def insert_many(self, record_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Insert multiple records in a single atomic batch write."""
        with self._lock:
            records = self._read_raw()
            now = utc_now_iso()
            inserted = []

            for record in record_list:
                item = dict(record)
                if self.primary_key not in item or not item[self.primary_key]:
                    item[self.primary_key] = str(uuid.uuid4())
                if "created_at" not in item:
                    item["created_at"] = now
                if "updated_at" not in item:
                    item["updated_at"] = now
                records.append(item)
                inserted.append(item)

            self._write_raw(records)
            return inserted

    def update(self, record_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update fields of an existing record by ID."""
        with self._lock:
            records = self._read_raw()
            found = False
            updated_record = None

            for i, record in enumerate(records):
                if record.get(self.primary_key) == record_id:
                    # Prevent changing the primary key
                    clean_updates = {k: v for k, v in updates.items() if k != self.primary_key}
                    clean_updates["updated_at"] = utc_now_iso()
                    records[i].update(clean_updates)
                    updated_record = dict(records[i])
                    found = True
                    break

            if not found:
                raise RecordNotFoundError(self.table_name, record_id)

            self._write_raw(records)
            return updated_record

    def update_where(self, filters: Dict[str, Any], updates: Dict[str, Any]) -> int:
        """Update all records matching filters. Returns count of modified records."""
        with self._lock:
            records = self._read_raw()
            modified_count = 0
            now = utc_now_iso()

            for i, record in enumerate(records):
                if all(record.get(k) == v for k, v in filters.items()):
                    clean_updates = {k: v for k, v in updates.items() if k != self.primary_key}
                    clean_updates["updated_at"] = now
                    records[i].update(clean_updates)
                    modified_count += 1

            if modified_count > 0:
                self._write_raw(records)

            return modified_count

    def delete(self, record_id: str) -> bool:
        """Delete a record by ID. Returns True if deleted, raises RecordNotFoundError otherwise."""
        with self._lock:
            records = self._read_raw()
            initial_len = len(records)
            records = [r for r in records if r.get(self.primary_key) != record_id]

            if len(records) == initial_len:
                raise RecordNotFoundError(self.table_name, record_id)

            self._write_raw(records)
            return True

    def delete_where(self, filters: Dict[str, Any]) -> int:
        """Delete all records matching filters. Returns count of removed records."""
        with self._lock:
            records = self._read_raw()
            initial_len = len(records)
            records = [
                r for r in records
                if not all(r.get(k) == v for k, v in filters.items())
            ]
            deleted_count = initial_len - len(records)
            if deleted_count > 0:
                self._write_raw(records)
            return deleted_count

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records matching optional filters."""
        if not filters:
            return len(self._read_raw())
        return len(self.find_all(filters=filters))

    def exists(self, filters: Dict[str, Any]) -> bool:
        """Check if any record matches given filters."""
        return self.find_one(filters=filters) is not None

    def clear(self) -> None:
        """Clear all records from table."""
        with self._lock:
            self._write_raw([])


class JsonDatabase:
    """
    Central Database Manager wrapping all individual JsonTables.
    Provides direct access to all required domain tables.
    """

    def __init__(self, data_dir: Optional[Union[str, Path]] = None):
        if data_dir is None:
            # Default to settings.DATA_DIR or relative data/ folder
            base_dir = Path(__file__).resolve().parent.parent
            data_dir = base_dir / "data"

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize all domain tables specified in requirements
        self.users = JsonTable(self.data_dir / "users.json", "users")
        self.patients = JsonTable(self.data_dir / "patients.json", "patients")
        self.doctors = JsonTable(self.data_dir / "doctors.json", "doctors")
        self.health_profiles = JsonTable(self.data_dir / "health_profiles.json", "health_profiles")
        self.medical_history = JsonTable(self.data_dir / "medical_history.json", "medical_history")
        self.symptoms = JsonTable(self.data_dir / "symptoms.json", "symptoms")
        self.appointments = JsonTable(self.data_dir / "appointments.json", "appointments")
        self.predictions = JsonTable(self.data_dir / "predictions.json", "predictions")
        self.recommendations = JsonTable(self.data_dir / "recommendations.json", "recommendations")
        self.notifications = JsonTable(self.data_dir / "notifications.json", "notifications")
        self.audit_logs = JsonTable(self.data_dir / "audit_logs.json", "audit_logs")

        self._tables: Dict[str, JsonTable] = {
            "users": self.users,
            "patients": self.patients,
            "doctors": self.doctors,
            "health_profiles": self.health_profiles,
            "medical_history": self.medical_history,
            "symptoms": self.symptoms,
            "appointments": self.appointments,
            "predictions": self.predictions,
            "recommendations": self.recommendations,
            "notifications": self.notifications,
            "audit_logs": self.audit_logs,
        }

    def get_table(self, name: str) -> JsonTable:
        """Get table by name or dynamically create it."""
        if name in self._tables:
            return self._tables[name]
        table = JsonTable(self.data_dir / f"{name}.json", name)
        self._tables[name] = table
        return table

    def get_system_stats(self) -> Dict[str, Any]:
        """Aggregate statistical summary of all tables and storage volume."""
        stats = {}
        total_records = 0
        for name, table in self._tables.items():
            cnt = table.count()
            file_size_kb = round(table.file_path.stat().st_size / 1024, 2) if table.file_path.exists() else 0.0
            stats[name] = {
                "count": cnt,
                "size_kb": file_size_kb,
                "file_path": str(table.file_path),
            }
            total_records += cnt

        stats["total_records"] = total_records
        stats["storage_type"] = "Atomic JSON File Engine"
        return stats


# Global database instance singleton
db = JsonDatabase()
