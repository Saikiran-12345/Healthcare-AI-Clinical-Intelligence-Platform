"""
CSV Storage and Data Interchange Utility for Healthcare AI Application.
Enables exporting JSON tables to CSV format, importing tabular datasets for ML training,
and producing clinical tabular data backups.
"""

import csv
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from core.exceptions import StorageError


class CsvStorage:
    """Utility class for CSV export, import, and dataset serialization."""

    @staticmethod
    def export_to_csv_file(records: List[Dict[str, Any]], target_file: Union[str, Path], fieldnames: Optional[List[str]] = None) -> Path:
        """Export a list of dictionary records to a CSV file on disk."""
        target_path = Path(target_file)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if not records:
            # Create an empty CSV or with headers if provided
            with open(target_path, "w", newline="", encoding="utf-8") as f:
                if fieldnames:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
            return target_path

        # Determine all distinct fieldnames if not provided
        if not fieldnames:
            keys = set()
            for r in records:
                keys.update(r.keys())
            fieldnames = sorted(list(keys))

        try:
            with open(target_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                for r in records:
                    # Flatten nested dicts/lists to JSON strings if needed
                    flat_row = {}
                    for k in fieldnames:
                        val = r.get(k)
                        if isinstance(val, (dict, list)):
                            import json
                            flat_row[k] = json.dumps(val)
                        else:
                            flat_row[k] = val if val is not None else ""
                    writer.writerow(flat_row)
            return target_path
        except Exception as e:
            raise StorageError(f"Failed to export records to CSV at '{target_path}': {str(e)}")

    @staticmethod
    def export_to_csv_string(records: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> str:
        """Export records to an in-memory CSV string for HTTP downloads."""
        output = io.StringIO()
        if not records:
            if fieldnames:
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
            return output.getvalue()

        if not fieldnames:
            keys = set()
            for r in records:
                keys.update(r.keys())
            fieldnames = sorted(list(keys))

        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for r in records:
            flat_row = {}
            for k in fieldnames:
                val = r.get(k)
                if isinstance(val, (dict, list)):
                    import json
                    flat_row[k] = json.dumps(val)
                else:
                    flat_row[k] = val if val is not None else ""
            writer.writerow(flat_row)

        return output.getvalue()

    @staticmethod
    def import_from_csv_file(source_file: Union[str, Path]) -> List[Dict[str, Any]]:
        """Read a CSV file and return a list of dictionaries."""
        source_path = Path(source_file)
        if not source_path.exists():
            raise StorageError(f"CSV file '{source_path}' does not exist.")

        records = []
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append(dict(row))
            return records
        except Exception as e:
            raise StorageError(f"Failed to parse CSV file '{source_path}': {str(e)}")
