"""Data models representing records, claims, citations, and findings."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class RawRow:
    """Represents a single raw line or entry in a record file."""
    file_name: str
    row_num: int  # 1-indexed line number in the source file
    raw_text: str  # exact unmodified raw text of the line/cue
    parsed_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    device: Optional[str] = None


@dataclass
class Claim:
    """Represents a factual claim extracted verbatim from an incident report."""
    text: str
    sentence_idx: int
    raw_sentence: str
    time_hint: Optional[str] = None
    speed_mph: Optional[int] = None
    zone_mph: Optional[int] = None
    entities: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


@dataclass
class Finding:
    """Represents an evaluated finding for a claim adhering to the exact schema."""
    claim: str
    finding: str  # "match" | "conflict" | "not_settled" | "not_checkable"
    cite: Optional[Dict[str, Any]] = None  # {"file": str, "row": int}
    quote: Optional[str] = None
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict according to strict schema rules.
        
        Rule: cite and quote are required for match and conflict,
        and must be omitted for not_settled and not_checkable.
        """
        res: Dict[str, Any] = {
            "claim": self.claim,
            "finding": self.finding,
        }
        if self.finding in ("match", "conflict"):
            if self.cite is not None:
                res["cite"] = self.cite
            if self.quote is not None:
                res["quote"] = self.quote
        return res
