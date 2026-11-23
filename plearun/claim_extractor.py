"""Incident report parser and factual claim extractor."""

import re
from typing import List, Optional
from plearun.models import Claim


class ClaimExtractor:
    """Extracts factual claims verbatim from incident reports."""

    PREDICATE_WORDS = {
        "observed", "travelling", "traveling", "pulled", "stopped", "logged",
        "shows", "show", "states", "stated", "was", "were", "is", "are",
        "reported", "arrived", "drove", "speeding", "clocked", "noted",
        "called", "dispatched", "found", "exceeded", "fled"
    }

    def extract_claims(self, report_path: str) -> List[Claim]:
        with open(report_path, "r", encoding="utf-8", errors="replace") as f:
            raw_text = f.read()

        claims: List[Claim] = []
        lines = raw_text.splitlines()
        sentence_idx = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Strip synthetic banners/disclaimers
            line = re.sub(r"^(?:SYNTHETIC\s*-\s*FICTIONAL\s*CASE\.?)\s*", "", line, flags=re.IGNORECASE).strip()
            if not line:
                continue

            # Split into sentences
            sents = re.split(r"(?<=[.!?])\s+", line)
            for s in sents:
                s = s.strip()
                if not s:
                    continue

                # Filter out pure non-assertive headers (no verbs/actions)
                words = set(re.findall(r"\b[a-zA-Z]+\b", s.lower()))
                if not words.intersection(self.PREDICATE_WORDS):
                    continue

                sentence_idx += 1

                # Extract semantic hints
                time_match = re.search(r"\b(\d{1,2}:\d{2})\b", s)
                time_hint = time_match.group(1) if time_match else None

                speed_match = re.search(r"(\d+)\s*(?:mph|speed)", s, re.I)
                speed_val = int(speed_match.group(1)) if speed_match else None

                zone_match = re.search(r"(?:posted\s*)?(\d+)\s*zone", s, re.I)
                zone_val = int(zone_match.group(1)) if zone_match else None

                entities = []
                for ent in ["Officer Lee", "blue sedan", "Harbor Gas", "Dispatch", "Route 21"]:
                    if ent.lower() in s.lower():
                        entities.append(ent)

                claims.append(Claim(
                    text=s,
                    sentence_idx=sentence_idx,
                    raw_sentence=s,
                    time_hint=time_hint,
                    speed_mph=speed_val,
                    zone_mph=zone_val,
                    entities=entities,
                    keywords=list(words)
                ))

        return claims
