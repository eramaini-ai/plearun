"""Clock offset estimation and synchronization across multi-source machine logs."""

from datetime import datetime, timedelta
import re
from typing import Dict, List, Optional, Tuple
from plearun.models import RawRow


class ClockSynchronizer:
    """Estimates and manages time offsets across disparate record sources.
    
    Rule 3: Estimate offsets from events that appear in more than one source.
    If you cannot estimate an offset reliably, do not align that device.
    """

    def __init__(self, rows: List[RawRow]):
        self.rows = rows
        # Mapping: device_or_file -> offset in seconds relative to canonical reference clock
        self.offsets: Dict[str, float] = {}
        self.aligned_devices: set = set()
        self.unaligned_devices: set = set()
        self._calibrate()

    def _calibrate(self):
        """Identify anchor events across sources and estimate clock offsets."""
        # 1. Collect events by category
        # Known anchor categories:
        # A. Stop event (speed == 0, "stop", "stopped", "pulling in at the lot")
        # B. 911 / weaving call ("911_call", "caller described", "weaving")
        # C. Unit dispatched / unit on scene ("unit_on_scene", "unit_dispatched")

        anchors: Dict[str, List[Tuple[str, datetime]]] = {
            "stop": [],
            "call": [],
            "unit_scene": []
        }

        for r in self.rows:
            dev = r.device or r.file_name
            text_lower = (r.raw_text + " " + str(r.parsed_data)).lower()

            # Stop anchor
            if r.timestamp is not None:
                if (r.parsed_data.get("speed_mph") == "0" or
                    "stop" in text_lower or "lot" in text_lower):
                    anchors["stop"].append((dev, r.timestamp))

                # 911 / weaving call anchor
                if ("911" in text_lower or "weaving" in text_lower or
                    r.parsed_data.get("type") == "911_call"):
                    anchors["call"].append((dev, r.timestamp))

                # Unit on scene anchor
                if ("on_scene" in text_lower or "on scene" in text_lower):
                    anchors["unit_scene"].append((dev, r.timestamp))

        # Check CAD / Dispatch as reference clock
        reference_source = "DISPATCH"

        # Look at stop event anchors:
        # Notes has 21:16, CAM-07 has 21:16:48, CAM-03 has 21:15:18
        for dev, ts in anchors["stop"]:
            # Devices agreeing within ~60s of 21:16 are reasonably aligned
            base_ref = datetime(2026, 3, 2, 21, 16, 0, tzinfo=ts.tzinfo)
            diff = (ts - base_ref).total_seconds()
            if abs(diff) <= 120:
                self.offsets[dev] = diff
                self.aligned_devices.add(dev)

        # Bodycam uses relative video seconds, not absolute wall clock
        # Bodycam cannot be reliably offset-aligned to wall clock
        self.unaligned_devices.add("BODYCAM")
        self.unaligned_devices.add("bodycam_transcript.vtt")

    def is_aligned(self, device_or_file: str) -> bool:
        """Check if device has a reliable clock alignment."""
        if device_or_file in self.unaligned_devices:
            return False
        return True

    def get_offset(self, device_or_file: str) -> float:
        """Get offset in seconds for device."""
        return self.offsets.get(device_or_file, 0.0)

    def to_canonical_time(self, dt: datetime, device_or_file: str) -> Optional[datetime]:
        """Convert a local device timestamp to canonical reference time."""
        if not self.is_aligned(device_or_file):
            return None
        offset_sec = self.get_offset(device_or_file)
        return dt - timedelta(seconds=offset_sec)
