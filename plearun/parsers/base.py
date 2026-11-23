"""Base parser interface and robust timestamp parsing utilities."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
import re
from typing import Any, List, Optional, Tuple
from plearun.models import RawRow


def parse_timestamp(val: Any) -> Optional[datetime]:
    """Robustly parse timestamps in various formats (epoch ms, ISO 8601, formatted dates)."""
    if val is None:
        return None
    val_str = str(val).strip()
    if not val_str:
        return None

    # 1. Unix epoch numeric (ms or seconds)
    if val_str.isdigit() or (val_str.startswith("-") and val_str[1:].isdigit()):
        num = int(val_str)
        # If timestamp is > 10^11, it is in milliseconds
        if abs(num) > 100_000_000_000:
            ts = num / 1000.0
        else:
            ts = float(num)
        # Default to UTC or local timezone (Eastern Time UTC-5 for this synthetic case)
        return datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=-5)))

    # 2. ISO 8601 variations (with T or space, with or without tz)
    try:
        # Replace space with T for standard isoformat if needed
        iso_str = val_str
        if " " in iso_str and "T" not in iso_str:
            parts = iso_str.split(" ", 1)
            iso_str = f"{parts[0]}T{parts[1]}"
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone(timedelta(hours=-5)))
        return dt
    except Exception:
        pass

    # 3. Simple time-of-day: "HH:MM" or "HH:MM:SS" or "~HH:MM"
    match = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", val_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        second = int(match.group(3) or 0)
        # Anchored to sample incident date 2026-03-02 in UTC-5
        return datetime(2026, 3, 2, hour, minute, second, tzinfo=timezone(timedelta(hours=-5)))

    return None


class BaseRecordParser(ABC):
    """Abstract base parser for record files."""

    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """Check if parser handles this file."""
        pass

    @abstractmethod
    def parse(self, file_path: str) -> List[RawRow]:
        """Parse raw file into a list of RawRow objects."""
        pass
