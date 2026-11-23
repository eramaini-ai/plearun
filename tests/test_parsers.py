"""Unit tests for record parsers."""

import os
import unittest
from plearun.parsers.csv_parser import RobustCSVParser
from plearun.parsers.json_parser import RobustJSONParser
from plearun.parsers.vtt_parser import RobustVTTParser
from plearun.parsers.base import parse_timestamp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestParsers(unittest.TestCase):
    def setUp(self):
        self.csv_parser = RobustCSVParser()
        self.json_parser = RobustJSONParser()
        self.vtt_parser = RobustVTTParser()

    def test_timestamp_parser(self):
        # Epoch ms
        dt_ms = parse_timestamp("1772502579000")
        self.assertIsNotNone(dt_ms)
        self.assertEqual(dt_ms.hour, 20)

        # ISO 8601 with tz
        dt_iso = parse_timestamp("2026-03-02T20:51:06-05:00")
        self.assertIsNotNone(dt_iso)
        self.assertEqual(dt_iso.minute, 51)

        # Date with space
        dt_sp = parse_timestamp("2026-03-02 21:10:19")
        self.assertIsNotNone(dt_sp)
        self.assertEqual(dt_sp.minute, 10)

        # Short time
        dt_short = parse_timestamp("21:15")
        self.assertIsNotNone(dt_short)
        self.assertEqual(dt_short.hour, 21)
        self.assertEqual(dt_short.minute, 15)

    def test_camera_log_parsing(self):
        cam_file = os.path.join(ROOT, "records/camera_log.csv")
        rows = self.csv_parser.parse(cam_file)
        self.assertTrue(len(rows) > 0)
        # Verify first data row line number is 3 (skipping marker line and header)
        self.assertEqual(rows[0].row_num, 3)
        self.assertIn("CAM-07", rows[0].raw_text)

    def test_cp1252_notes_parsing(self):
        notes_file = os.path.join(ROOT, "records/notes_cp1252.csv")
        rows = self.csv_parser.parse(notes_file)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0].row_num, 2)
        self.assertEqual(rows[0].parsed_data["id"], "N-1")

    def test_dispatch_json_parsing(self):
        disp_file = os.path.join(ROOT, "records/dispatch.json")
        rows = self.json_parser.parse(disp_file)
        self.assertTrue(len(rows) >= 3)
        # Check event D-1001
        found_call = any(r.parsed_data.get("id") == "D-1001" for r in rows)
        self.assertTrue(found_call)

    def test_vtt_parsing(self):
        vtt_file = os.path.join(ROOT, "records/bodycam_transcript.vtt")
        rows = self.vtt_parser.parse(vtt_file)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0].parsed_data["cue_number"], 1)
        self.assertEqual(rows[0].row_num, 4)
        self.assertIn("58 in a 45.", rows[0].raw_text)


if __name__ == "__main__":
    unittest.main()
