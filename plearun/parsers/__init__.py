"""Parser registration and loader utilities."""

import os
from typing import Dict, List
from plearun.models import RawRow
from plearun.parsers.base import BaseRecordParser
from plearun.parsers.csv_parser import RobustCSVParser
from plearun.parsers.json_parser import RobustJSONParser
from plearun.parsers.vtt_parser import RobustVTTParser


PARSERS: List[BaseRecordParser] = [
    RobustCSVParser(),
    RobustJSONParser(),
    RobustVTTParser()
]


def load_records_dir(records_dir: str) -> List[RawRow]:
    """Parse all supported files in records_dir into a flat list of RawRow objects."""
    all_rows: List[RawRow] = []
    if not os.path.exists(records_dir):
        return all_rows

    for entry in sorted(os.listdir(records_dir)):
        full_path = os.path.join(records_dir, entry)
        if not os.path.isfile(full_path):
            continue

        for parser in PARSERS:
            if parser.can_parse(full_path):
                file_rows = parser.parse(full_path)
                all_rows.extend(file_rows)
                break

    return all_rows
