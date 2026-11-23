"""Robust CSV parser handling UTF-8 BOM, cp1252, comments (#), and varying schemas."""

import csv
import io
import os
from typing import List, Optional
from plearun.models import RawRow
from plearun.parsers.base import BaseRecordParser, parse_timestamp


class RobustCSVParser(BaseRecordParser):
    """Parses CSV files with automatic encoding detection, comment skipping, and row tracking."""

    SUPPORTED_ENCODINGS = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]

    def can_parse(self, file_path: str) -> bool:
        return file_path.lower().endswith(".csv")

    def _read_lines(self, file_path: str) -> List[str]:
        """Read lines trying supported encodings."""
        for enc in self.SUPPORTED_ENCODINGS:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read().splitlines()
            except (UnicodeDecodeError, UnicodeError):
                continue
        # Fallback with error replacement
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()

    def parse(self, file_path: str) -> List[RawRow]:
        lines = self._read_lines(file_path)
        file_name = os.path.basename(file_path)
        rows: List[RawRow] = []

        header: Optional[List[str]] = None
        header_row_idx: int = -1

        for idx, line in enumerate(lines, start=1):
            raw_text = line.rstrip("\r\n")
            stripped = raw_text.strip()

            # Skip empty lines
            if not stripped:
                continue

            # Skip leading comments / marker lines (e.g. #PLEARUN ...)
            if stripped.startswith("#"):
                continue

            # Parse line with csv reader
            reader = csv.reader(io.StringIO(raw_text))
            try:
                fields = next(reader)
            except Exception:
                fields = [f.strip() for f in raw_text.split(",")]

            if header is None:
                # First non-comment row is the CSV header
                header = [f.strip().lower() for f in fields]
                header_row_idx = idx
                continue

            # Build parsed data map
            data = {}
            for col_idx, col_name in enumerate(header):
                if col_idx < len(fields):
                    data[col_name] = fields[col_idx].strip()

            # Extract common attributes
            ts_val = data.get("timestamp") or data.get("time") or data.get("logged")
            dt = parse_timestamp(ts_val)

            dev = data.get("device") or data.get("unit") or data.get("author")

            rows.append(RawRow(
                file_name=file_name,
                row_num=idx,
                raw_text=raw_text,
                parsed_data=data,
                timestamp=dt,
                device=dev
            ))

        return rows
