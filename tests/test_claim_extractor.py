"""Unit tests for report claim extraction."""

import os
import unittest
from plearun.claim_extractor import ClaimExtractor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestClaimExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = ClaimExtractor()
        self.report_path = os.path.join(ROOT, "reports/report_fictional_02.txt")

    def test_extract_sample_claims(self):
        claims = self.extractor.extract_claims(self.report_path)
        # Should extract 5 substantive claims, skipping synthetic disclaimer and pure title
        self.assertEqual(len(claims), 5)

        # First claim should mention 58 mph and 45 zone
        self.assertIn("58 mph", claims[0].text)
        self.assertEqual(claims[0].speed_mph, 58)
        self.assertEqual(claims[0].zone_mph, 45)

        # Second claim should mention 21:16
        self.assertIn("21:16", claims[1].text)

        # Third claim should mention 911 call and 21:11
        self.assertIn("911 call", claims[2].text)
        self.assertIn("21:11", claims[2].text)

        # Fourth claim should mention unit on scene
        self.assertIn("unit on scene", claims[3].text)

        # Fifth claim should mention only car in the lane
        self.assertIn("only car in the lane", claims[4].text)


if __name__ == "__main__":
    unittest.main()
