"""Unit tests for clock synchronization and device offset estimation."""

import os
import unittest
from plearun.parsers import load_records_dir
from plearun.time_sync import ClockSynchronizer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestClockSync(unittest.TestCase):
    def setUp(self):
        records_dir = os.path.join(ROOT, "records")
        self.rows = load_records_dir(records_dir)
        self.clock_sync = ClockSynchronizer(self.rows)

    def test_bodycam_is_unaligned(self):
        # Bodycam has relative video timestamps, cannot align reliably to wall clock
        self.assertFalse(self.clock_sync.is_aligned("BODYCAM"))
        self.assertFalse(self.clock_sync.is_aligned("bodycam_transcript.vtt"))

    def test_anchor_offset_computation(self):
        # CAM-07 stopped at 21:16:48, base ref is 21:16:00 -> offset is 48.0s
        offset = self.clock_sync.get_offset("CAM-07")
        self.assertAlmostEqual(offset, 48.0, delta=1.0)


if __name__ == "__main__":
    unittest.main()
