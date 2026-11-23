"""Unit tests for Rule 1 substring verification and schema downgrade enforcement."""

import os
import unittest
from plearun.models import Finding
from plearun.validator import FindingValidator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestFindingValidator(unittest.TestCase):
    def setUp(self):
        records_dir = os.path.join(ROOT, "records")
        self.validator = FindingValidator(records_dir)

    def test_valid_match_passes(self):
        finding = Finding(
            claim="Vehicle stopped around 21:16",
            finding="match",
            cite={"file": "notes_cp1252.csv", "row": 4},
            quote="Stopped at lot ~21:16"
        )
        res = self.validator.validate_and_finalize(finding)
        self.assertEqual(res.finding, "match")
        self.assertEqual(res.cite["file"], "notes_cp1252.csv")
        self.assertEqual(res.cite["row"], 4)
        self.assertEqual(res.quote, "Stopped at lot ~21:16")

    def test_invalid_quote_downgrades_to_not_settled(self):
        # Quote that is NOT in row 4
        finding = Finding(
            claim="Vehicle stopped around 21:16",
            finding="match",
            cite={"file": "notes_cp1252.csv", "row": 4},
            quote="THIS QUOTE DOES NOT EXIST IN ROW 4"
        )
        res = self.validator.validate_and_finalize(finding)
        # Must downgrade to not_settled and strip cite and quote
        self.assertEqual(res.finding, "not_settled")
        self.assertIsNone(res.cite)
        self.assertIsNone(res.quote)

    def test_out_of_bounds_row_downgrades_to_not_settled(self):
        finding = Finding(
            claim="Vehicle stopped around 21:16",
            finding="match",
            cite={"file": "notes_cp1252.csv", "row": 9999},
            quote="Stopped at lot ~21:16"
        )
        res = self.validator.validate_and_finalize(finding)
        self.assertEqual(res.finding, "not_settled")
        self.assertIsNone(res.cite)
        self.assertIsNone(res.quote)

    def test_not_checkable_omits_cite_and_quote(self):
        finding = Finding(
            claim="Vehicle was the only car in the lane",
            finding="not_checkable",
            cite={"file": "notes_cp1252.csv", "row": 2},
            quote="Officer Lee"
        )
        res = self.validator.validate_and_finalize(finding)
        self.assertEqual(res.finding, "not_checkable")
        self.assertIsNone(res.cite)
        self.assertIsNone(res.quote)
        d = res.to_dict()
        self.assertNotIn("cite", d)
        self.assertNotIn("quote", d)


if __name__ == "__main__":
    unittest.main()
