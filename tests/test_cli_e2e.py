"""End-to-end CLI integration tests verifying exact schema compliance."""

import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestCLIE2E(unittest.TestCase):
    def test_cli_execution_and_schema(self):
        cli_path = os.path.join(ROOT, "plearun_cli.py")
        report_path = os.path.join(ROOT, "reports/report_fictional_02.txt")
        records_dir = os.path.join(ROOT, "records")

        proc = subprocess.run(
            [sys.executable, cli_path, report_path, records_dir],
            capture_output=True,
            text=True,
            cwd=ROOT
        )
        self.assertEqual(proc.returncode, 0, f"CLI exited with error: {proc.stderr}")

        data = json.loads(proc.stdout)
        self.assertIn("findings", data)
        findings = data["findings"]
        self.assertGreater(len(findings), 0)

        valid_findings = {"match", "conflict", "not_settled", "not_checkable"}

        for item in findings:
            self.assertIn("claim", item)
            self.assertIn("finding", item)
            self.assertIn(item["finding"], valid_findings)

            if item["finding"] in ("match", "conflict"):
                self.assertIn("cite", item)
                self.assertIn("file", item["cite"])
                self.assertIn("row", item["cite"])
                self.assertIsInstance(item["cite"]["row"], int)
                self.assertIn("quote", item)

                # Verify Rule 1 on the actual output: quote MUST be substring of row
                target_file = os.path.join(records_dir, item["cite"]["file"])
                self.assertTrue(os.path.exists(target_file))

                # Read raw line
                for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
                    try:
                        with open(target_file, "r", encoding=enc) as f:
                            lines = f.read().splitlines()
                            break
                    except Exception:
                        continue

                row_idx = item["cite"]["row"]
                self.assertGreaterEqual(row_idx, 1)
                self.assertLessEqual(row_idx, len(lines))
                raw_row = lines[row_idx - 1]
                self.assertIn(
                    item["quote"],
                    raw_row,
                    f"Quote '{item['quote']}' is not an exact substring of row {row_idx}: '{raw_row}'"
                )

            else:
                # Rule 2: cite and quote must be omitted for not_settled and not_checkable
                self.assertNotIn("cite", item)
                self.assertNotIn("quote", item)


if __name__ == "__main__":
    unittest.main()
