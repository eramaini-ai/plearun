"""Robust JSON parser handling nested CAD dispatch exports and line-level mapping."""

import json
import os
import re
from typing import Any, Dict, List, Optional
from plearun.models import RawRow
from plearun.parsers.base import BaseRecordParser, parse_timestamp


class RobustJSONParser(BaseRecordParser):
    """Parses JSON logs while tracking line numbers for strict quote verification."""

    def can_parse(self, file_path: str) -> bool:
        return file_path.lower().endswith(".json")

    def parse(self, file_path: str) -> List[RawRow]:
        file_name = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            raw_lines = f.read().splitlines()

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            try:
                data = json.load(f)
            except Exception:
                return []

        rows: List[RawRow] = []

        # Find events list in JSON structure
        events = []
        if isinstance(data, list):
            events = data
        elif isinstance(data, dict):
            if "export" in data and isinstance(data["export"], dict) and "events" in data["export"]:
                events = data["export"]["events"]
            elif "events" in data and isinstance(data["events"], list):
                events = data["events"]
            else:
                # Flat or custom object
                events = [data]

        for ev in events:
            if not isinstance(ev, dict):
                continue

            ev_id = str(ev.get("id", ""))
            ev_type = str(ev.get("type", ""))
            logged_val = ev.get("logged") or ev.get("timestamp") or ev.get("time")
            unit_val = str(ev.get("unit", ""))
            dt = parse_timestamp(logged_val)

            # Find line numbers in raw_lines for id, type, and logged
            id_line = -1
            type_line = -1
            logged_line = -1

            logged_str = str(logged_val) if logged_val is not None else ""

            for idx, line in enumerate(raw_lines, start=1):
                if ev_id and f'"{ev_id}"' in line:
                    id_line = idx
                if ev_type and f'"{ev_type}"' in line:
                    type_line = idx
                if logged_str and logged_str in line:
                    logged_line = idx

            # Add entries for line-level citations
            # 1. Primary row pointing to the logged timestamp line if available
            primary_row = logged_line if logged_line != -1 else (type_line if type_line != -1 else (id_line if id_line != -1 else 1))
            primary_text = raw_lines[primary_row - 1] if 0 < primary_row <= len(raw_lines) else ""

            rows.append(RawRow(
                file_name=file_name,
                row_num=primary_row,
                raw_text=primary_text,
                parsed_data={
                    "event": ev,
                    "id": ev_id,
                    "type": ev_type,
                    "logged": logged_str,
                    "unit": unit_val,
                    "logged_line": logged_line,
                    "type_line": type_line,
                    "id_line": id_line
                },
                timestamp=dt,
                device=unit_val or "DISPATCH"
            ))

            # Also add direct line-level rows so any citation to type_line or id_line is known
            if type_line != -1 and type_line != primary_row:
                rows.append(RawRow(
                    file_name=file_name,
                    row_num=type_line,
                    raw_text=raw_lines[type_line - 1],
                    parsed_data={"event": ev, "type": ev_type, "id": ev_id},
                    timestamp=dt,
                    device=unit_val or "DISPATCH"
                ))

        return rows
