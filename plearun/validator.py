"""Strict validator enforcing Rule 1 and quote verification guarantees."""

import os
from typing import List, Optional
from plearun.models import Finding


class FindingValidator:
    """Enforces Rule 1 (exact substring verification) and schema constraints.
    
    Rule 1: Every match or conflict must cite a real row, and your code
    must verify the quote is an exact substring of the raw text of that row
    before the finding is written. Otherwise downgrade to not_settled.
    
    Rule 2: cite and quote are required for match and conflict,
    and must be omitted for not_settled and not_checkable.
    """

    def __init__(self, records_dir: str):
        self.records_dir = records_dir
        self._raw_lines_cache = {}

    def _get_raw_lines(self, filename: str) -> Optional[List[str]]:
        if filename in self._raw_lines_cache:
            return self._raw_lines_cache[filename]

        filepath = os.path.join(self.records_dir, filename)
        if not os.path.exists(filepath):
            return None

        # Try multiple encodings to read exactly as encoded
        encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
        for enc in encodings:
            try:
                with open(filepath, "r", encoding=enc) as f:
                    lines = f.read().splitlines()
                    self._raw_lines_cache[filename] = lines
                    return lines
            except Exception:
                continue

        # Fallback with replace
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
            self._raw_lines_cache[filename] = lines
            return lines

    def validate_and_finalize(self, finding: Finding) -> Finding:
        """Validate finding and enforce Rule 1 substring verification."""
        if finding.finding in ("match", "conflict"):
            # Must have cite and quote
            if not finding.cite or not finding.quote:
                finding.finding = "not_settled"
                finding.cite = None
                finding.quote = None
                return finding

            filename = finding.cite.get("file")
            row_num = finding.cite.get("row")

            if not filename or not isinstance(row_num, int) or row_num <= 0:
                finding.finding = "not_settled"
                finding.cite = None
                finding.quote = None
                return finding

            raw_lines = self._get_raw_lines(filename)
            if raw_lines is None or row_num > len(raw_lines):
                # Row out of bounds
                finding.finding = "not_settled"
                finding.cite = None
                finding.quote = None
                return finding

            raw_row_text = raw_lines[row_num - 1]

            # Rule 1 exact substring verification
            if finding.quote not in raw_row_text:
                # Quote is not an exact substring of raw text -> downgrade to not_settled
                finding.finding = "not_settled"
                finding.cite = None
                finding.quote = None
                return finding

        elif finding.finding in ("not_settled", "not_checkable"):
            # Must omit cite and quote
            finding.cite = None
            finding.quote = None

        return finding

    def validate_all(self, findings: List[Finding]) -> List[Finding]:
        return [self.validate_and_finalize(f) for f in findings]
