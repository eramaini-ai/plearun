"""Robust WebVTT parser handling timestamps, cue text, speaker tags, and line mapping."""

import os
import re
from typing import List, Optional
from plearun.models import RawRow
from plearun.parsers.base import BaseRecordParser


class RobustVTTParser(BaseRecordParser):
    """Parses WebVTT files into cue-based and line-based RawRows."""

    def can_parse(self, file_path: str) -> bool:
        return file_path.lower().endswith(".vtt")

    def _parse_vtt_timestamp(self, ts_str: str) -> float:
        """Parse WebVTT timestamp (HH:MM:SS.mmm or MM:SS.mmm) to total seconds."""
        ts_str = ts_str.strip()
        parts = ts_str.split(":")
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        return 0.0

    def parse(self, file_path: str) -> List[RawRow]:
        file_name = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            raw_lines = f.read().splitlines()

        rows: List[RawRow] = []
        cue_idx = 0
        current_start: Optional[float] = None
        current_end: Optional[float] = None

        time_pattern = re.compile(r"((?:\d{2}:)?\d{2}:\d{2}\.\d{3})\s*-->\s*((?:\d{2}:)?\d{2}:\d{2}\.\d{3})")

        for idx, line in enumerate(raw_lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("WEBVTT") or stripped.startswith("NOTE"):
                continue

            time_match = time_pattern.search(stripped)
            if time_match:
                cue_idx += 1
                current_start = self._parse_vtt_timestamp(time_match.group(1))
                current_end = self._parse_vtt_timestamp(time_match.group(2))
                continue

            # This is a cue text line
            speaker = None
            text = stripped
            if ":" in stripped:
                prefix, body = stripped.split(":", 1)
                # Clean any tags like [SYNTHETIC]
                clean_speaker = re.sub(r"\[.*?\]", "", prefix).strip()
                if clean_speaker:
                    speaker = clean_speaker
                    text = body.strip()

            rows.append(RawRow(
                file_name=file_name,
                row_num=idx,  # exact 1-indexed line number in raw file
                raw_text=line,
                parsed_data={
                    "cue_number": cue_idx,
                    "start_sec": current_start,
                    "end_sec": current_end,
                    "speaker": speaker,
                    "text": text
                },
                timestamp=None,  # relative video elapsed time
                device="BODYCAM"
            ))

        return rows
